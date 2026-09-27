"""PostgreSQL session lifecycle, replay and multi-connection refresh tests."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy import select, delete, text

from app.main import app
from app.auth.models import AuthSession
from app.users.models import User
from app.auth.service import (
    decode_access_token,
    decode_refresh_token,
    create_access_token,
    create_refresh_token,
)
from app.config import get_settings


async def signup(client):
    key = uuid4().hex
    data = dict(
        email=f"{key}@example.com",
        username=key,
        password="correct password 123",
        full_name="Session Test",
    )
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 201
    return response.json()["id"], dict(email=data["email"], password=data["password"])


async def login(client, credentials):
    response = await client.post("/api/v1/auth/login", json=credentials)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


async def refresh(client, token):
    return await client.post("/api/v1/auth/refresh", json={"refresh_token": token})


def bearer(pair):
    return {"Authorization": f"Bearer {pair['access_token']}"}


async def test_login_persists_session_and_rotates(test_client_with_db, test_db_session):
    client = test_client_with_db
    uid, credentials = await signup(client)
    pair = await login(client, credentials)
    claims = decode_refresh_token(pair["refresh_token"])
    session = await test_db_session.get(AuthSession, claims["sid"])
    assert (
        session is not None and str(session.user_id) == uid and session.generation == 0
    )
    assert session.revoked_at is None
    assert claims["exp"] > decode_access_token(pair["access_token"])["exp"]
    assert (
        await client.get("/api/v1/auth/me", headers=bearer(pair))
    ).status_code == 200
    result = await refresh(client, pair["refresh_token"])
    assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
    rotated = result.json()
    assert rotated["refresh_token"] != pair["refresh_token"]
    newer = decode_refresh_token(rotated["refresh_token"])
    assert (
        newer["generation"] == 1
        and newer["sid"] == claims["sid"]
        and newer["exp"] == claims["exp"]
    )
    await test_db_session.refresh(session)
    assert session.generation == 1
    # A normal refresh does not invalidate still-unexpired access for the session.
    assert (
        await client.get("/api/v1/auth/me", headers=bearer(pair))
    ).status_code == 200
    assert (await refresh(client, rotated["refresh_token"])).status_code == 200
    assert not {"role", "roles", "is_super_admin", "hackathon_id"}.intersection(claims)


async def test_reuse_revokes_entire_session_and_descendants(
    test_client_with_db, test_db_session
):
    client = test_client_with_db
    _, credentials = await signup(client)
    old = await login(client, credentials)
    new = (await refresh(client, old["refresh_token"])).json()
    assert (await refresh(client, old["refresh_token"])).status_code == 401
    session = await test_db_session.get(
        AuthSession, decode_refresh_token(old["refresh_token"])["sid"]
    )
    await test_db_session.refresh(session)
    assert session.revoked_at is not None
    for pair in (old, new):
        assert (
            await client.get("/api/v1/auth/me", headers=bearer(pair))
        ).status_code == 401
        assert (await refresh(client, pair["refresh_token"])).status_code == 401


async def test_current_logout_preserves_other_session(
    test_client_with_db, test_db_session
):
    client = test_client_with_db
    uid, credentials = await signup(client)
    first, second = await login(client, credentials), await login(client, credentials)
    assert (
        await client.post("/api/v1/auth/logout", headers=bearer(first))
    ).status_code == 204
    assert (
        await client.get("/api/v1/auth/me", headers=bearer(first))
    ).status_code == 401
    assert (await refresh(client, first["refresh_token"])).status_code == 401
    assert (
        await client.get("/api/v1/auth/me", headers=bearer(second))
    ).status_code == 200
    assert (await refresh(client, second["refresh_token"])).status_code == 200
    assert (
        await test_db_session.scalar(select(User.auth_version).where(User.id == uid))
        == 1
    )


async def test_logout_all_scoped_to_one_user(test_client_with_db):
    client = test_client_with_db
    _, credentials = await signup(client)
    _, other_credentials = await signup(client)
    pairs = [await login(client, credentials) for _ in range(2)]
    other = await login(client, other_credentials)
    assert (
        await client.post("/api/v1/auth/logout-all", headers=bearer(pairs[0]))
    ).status_code == 204
    for pair in pairs:
        assert (
            await client.get("/api/v1/auth/me", headers=bearer(pair))
        ).status_code == 401
        assert (await refresh(client, pair["refresh_token"])).status_code == 401
    assert (
        await client.get("/api/v1/auth/me", headers=bearer(other))
    ).status_code == 200
    assert (await refresh(client, other["refresh_token"])).status_code == 200
    assert (
        decode_access_token((await login(client, credentials))["access_token"])[
            "auth_version"
        ]
        == 2
    )


@pytest.mark.parametrize("change", ["disabled", "version"])
async def test_refresh_reloads_account_state(
    test_client_with_db, test_db_session, change
):
    client = test_client_with_db
    uid, credentials = await signup(client)
    pair = await login(client, credentials)
    clause = (
        "disabled_at=clock_timestamp()"
        if change == "disabled"
        else "auth_version=auth_version+1"
    )
    await test_db_session.execute(
        text(f"UPDATE dogfood.users SET {clause} WHERE id=:id"), {"id": uid}
    )
    await test_db_session.commit()
    assert (await refresh(client, pair["refresh_token"])).status_code == 401
    assert (
        await client.get("/api/v1/auth/me", headers=bearer(pair))
    ).status_code == 401


@pytest.mark.parametrize(
    "change",
    [
        {"type": "access"},
        {"sub": "bad"},
        {"sid": "bad"},
        {"sid": None},
        {"generation": None},
        {"generation": True},
        {"generation": "0"},
        {"generation": -1},
        {"generation": 2**63},
        {"auth_version": True},
        {"auth_version": None},
        {"exp": 1},
        {"exp": None},
        {"exp": float("inf")},
        {"iat": None},
        {"iat": 9999999999},
        {"iss": "wrong"},
        {"aud": "wrong"},
    ],
)
async def test_refresh_strict_claims(test_client_with_db, change):
    client = test_client_with_db
    _, credentials = await signup(client)
    pair = await login(client, credentials)
    claims = decode_refresh_token(pair["refresh_token"])
    claims.update(change)
    claims = {key: value for key, value in claims.items() if value is not None}
    token = jwt.encode(claims, get_settings().jwt_secret_key, algorithm="HS256")
    result = await refresh(client, token)
    assert result.status_code == 401
    assert result.json()["error"]["message"] == "Could not validate credentials"
    # Invalid claims must not let an unauthenticated request revoke a session.
    assert (await refresh(client, pair["refresh_token"])).status_code == 200


async def test_bad_signature_types_and_secrets_not_leaked(
    test_client_with_db, test_db_session, caplog
):
    client = test_client_with_db
    _, credentials = await signup(client)
    pair = await login(client, credentials)
    assert (await refresh(client, pair["access_token"])).status_code == 401
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {pair['refresh_token']}"}
    )
    assert response.status_code == 401
    claims = decode_refresh_token(pair["refresh_token"])
    bad = jwt.encode(claims, "x" * 32, algorithm="HS256")
    assert (await refresh(client, bad)).status_code == 401
    assert (await refresh(client, "invalid.token")).status_code == 401
    data = (
        await test_db_session.execute(
            text(
                "SELECT row_to_json(s)::text FROM dogfood.auth_sessions s WHERE id=:id"
            ),
            {"id": claims["sid"]},
        )
    ).scalar_one()
    me = await client.get("/api/v1/auth/me", headers=bearer(pair))
    for secret in (
        pair["access_token"],
        pair["refresh_token"],
        credentials["password"],
    ):
        assert (
            secret not in data and secret not in me.text and secret not in caplog.text
        )
    assert "refresh_token" not in data


async def test_session_expiry_and_ownership_enforced(
    test_client_with_db, test_db_session
):
    client = test_client_with_db
    uid, credentials = await signup(client)
    other_uid, _ = await signup(client)
    pair = await login(client, credentials)
    sid = decode_refresh_token(pair["refresh_token"])["sid"]
    forged_access = create_access_token(other_uid, 1, sid)
    assert (
        await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {forged_access}"}
        )
    ).status_code == 401
    claims = decode_refresh_token(pair["refresh_token"])
    claims["sub"] = other_uid
    forged_refresh = jwt.encode(
        claims, get_settings().jwt_secret_key, algorithm="HS256"
    )
    assert (await refresh(client, forged_refresh)).status_code == 401
    expired = AuthSession(
        user_id=uid,
        auth_version=1,
        created_at=datetime.now(timezone.utc) - timedelta(days=2),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    test_db_session.add(expired)
    await test_db_session.flush()
    token = create_access_token(uid, 1, str(expired.id))
    assert (
        await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
    ).status_code == 401
    # A signed future expiry does not override the stored session deadline.
    token = create_refresh_token(
        uid, 1, str(expired.id), 0, datetime.now(timezone.utc) + timedelta(days=1)
    )
    assert (await refresh(client, token)).status_code == 401


async def test_simultaneous_refresh_uses_database_locks(test_engine):
    """Two independent real HTTP sessions/connections, with a DB-held lock barrier."""
    assert not app.dependency_overrides
    uid = None
    tasks = []
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            uid, credentials = await signup(client)
            pair = await login(client, credentials)
            sid = decode_refresh_token(pair["refresh_token"])["sid"]
            async with test_engine.connect() as gate:
                tx = await gate.begin()
                await gate.execute(
                    text("SELECT id FROM dogfood.users WHERE id=:id FOR UPDATE"),
                    {"id": uid},
                )
                tasks = [
                    asyncio.create_task(refresh(client, pair["refresh_token"]))
                    for _ in range(2)
                ]
                # Observe both independent requests blocked on PostgreSQL locks before releasing.
                async with test_engine.connect() as observer:
                    for _ in range(200):
                        waiting = await observer.scalar(
                            text(
                                "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE '%dogfood.users%FOR UPDATE%'"
                            )
                        )
                        await observer.rollback()  # refresh pg_stat_activity snapshot
                        if waiting >= 2:
                            break
                        await asyncio.sleep(0.01)
                    else:
                        raise AssertionError(
                            "both refresh requests did not reach DB lock"
                        )
                await tx.commit()
            results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
            assert sorted(r.status_code for r in results) == [200, 401]
            winner = next(r.json() for r in results if r.status_code == 200)
            assert (await refresh(client, winner["refresh_token"])).status_code == 401
            assert (
                await client.get("/api/v1/auth/me", headers=bearer(winner))
            ).status_code == 401
            async with test_engine.connect() as connection:
                generation, revoked = (
                    await connection.execute(
                        text(
                            "SELECT generation,revoked_at FROM dogfood.auth_sessions WHERE id=:id"
                        ),
                        {"id": sid},
                    )
                ).one()
                assert generation == 1 and revoked is not None
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if uid:
            async with test_engine.begin() as connection:
                await connection.execute(
                    delete(AuthSession).where(AuthSession.user_id == uid)
                )
                await connection.execute(delete(User).where(User.id == uid))
