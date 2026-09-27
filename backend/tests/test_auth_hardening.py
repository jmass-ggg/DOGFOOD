"""T3 security and real transaction regressions; no mocked JWT validation."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import patch

import pytest
from jose import jwt
from sqlalchemy import select, text, delete
from httpx import AsyncClient, ASGITransport

from app.auth.service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    DUMMY_PASSWORD_HASH,
)
from app.auth.schemas import UserRegisterRequest
from app.config import get_settings, Settings
from app.main import app
from app.users.models import User
from app.auth.models import AuthSession


async def register(client, **overrides):
    key = uuid4().hex
    data = dict(
        email=f"{key}@example.com",
        username=key,
        password="Valid password 123",
        full_name="Test User",
    )
    data.update(overrides)
    response = await client.post("/api/v1/auth/register", json=data)
    return response, data


@pytest.mark.parametrize(
    "field",
    [
        "is_super_admin",
        "auth_version",
        "disabled_at",
        "password_hash",
        "email_verified_at",
    ],
)
async def test_registration_rejects_internal_fields(test_client_with_db, field):
    response, _ = await register(test_client_with_db, **{field: True})
    assert response.status_code == 422


async def test_username_canonical_conflict_and_session_recovery(test_client_with_db):
    first, data = await register(test_client_with_db)
    assert first.status_code == 201
    duplicate, _ = await register(
        test_client_with_db, username=" " + data["username"].upper() + " "
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["message"] == "Username already registered"
    assert (await register(test_client_with_db))[0].status_code == 201


async def test_nonexistent_login_verifies_precomputed_hash(test_client_with_db):
    import app.auth.router as router

    original = router.verify_password
    with patch.object(
        router, "verify_password", wraps=original
    ) as verifier, patch.object(
        router, "hash_password", side_effect=AssertionError("must not hash per login")
    ):
        response = await test_client_with_db.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "candidate"},
        )
    assert response.status_code == 401
    verifier.assert_called_once_with("candidate", DUMMY_PASSWORD_HASH)


@pytest.mark.parametrize(
    "change",
    [
        {"type": "refresh"},
        {"type": None},
        {"sub": "not-a-uuid"},
        {"sub": 123},
        {"sub": None},
        {"exp": None},
        {"exp": "9999999999"},
        {"exp": True},
        {"iat": None},
        {"auth_version": None},
        {"auth_version": True},
        {"auth_version": "1"},
        {"auth_version": 0},
        {"iss": "another-app"},
        {"aud": "another-app"},
        {"exp": 1},
        {"sub": str(uuid4())},
    ],
)
async def test_invalid_claims_rejected(test_client_with_db, change):
    created, _ = await register(test_client_with_db)
    claims = decode_access_token(create_access_token(created.json()["id"]))
    claims.update(change)
    for key in list(claims):
        if claims[key] is None:
            del claims[key]
    settings = get_settings()
    token = jwt.encode(claims, settings.jwt_secret_key, algorithm="HS256")
    response = await test_client_with_db.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["message"] == "Could not validate credentials"


async def test_auth_version_and_disabled_state_enforced(
    test_client_with_db, test_db_session
):
    created, data = await register(test_client_with_db)
    uid = created.json()["id"]
    login = await test_client_with_db.post(
        "/api/v1/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    token = login.json()["access_token"]
    assert login.headers["cache-control"] == "no-store"
    assert decode_access_token(token)["auth_version"] == 1
    await test_db_session.execute(
        text("UPDATE dogfood.users SET auth_version=2 WHERE id=:id"), {"id": uid}
    )
    await test_db_session.commit()
    assert (
        await test_client_with_db.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
    ).status_code == 401
    login = await test_client_with_db.post(
        "/api/v1/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    token = login.json()["access_token"]
    assert decode_access_token(token)["auth_version"] == 2
    await test_db_session.execute(
        text("UPDATE dogfood.users SET disabled_at=clock_timestamp() WHERE id=:id"),
        {"id": uid},
    )
    await test_db_session.commit()
    assert (
        await test_client_with_db.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
    ).status_code == 401
    disabled = await test_client_with_db.post(
        "/api/v1/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    unknown = await test_client_with_db.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": data["password"]},
    )
    assert disabled.status_code == unknown.status_code == 401
    assert disabled.json()["error"] == unknown.json()["error"]


async def test_logout_revokes_all_prior_access_credentials(test_client_with_db):
    _, data = await register(test_client_with_db)
    payload = {"email": data["email"], "password": data["password"]}
    tokens = [
        (await test_client_with_db.post("/api/v1/auth/login", json=payload)).json()[
            "access_token"
        ]
        for _ in range(2)
    ]
    response = await test_client_with_db.post(
        "/api/v1/auth/logout-all", headers={"Authorization": f"Bearer {tokens[0]}"}
    )
    assert response.status_code == 204
    for token in tokens:
        assert (
            await test_client_with_db.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
        ).status_code == 401
    login = await test_client_with_db.post("/api/v1/auth/login", json=payload)
    assert decode_access_token(login.json()["access_token"])["auth_version"] == 2
    assert (
        await test_client_with_db.post("/api/v1/auth/logout-all")
    ).status_code == 401


def test_argon2id_and_corrupt_hash():
    assert hash_password("password").startswith("$argon2id$")
    assert verify_password("password", "corrupted-hash") is False


@pytest.mark.parametrize(
    "value", ["", "short", " " * 32, "your-secret-key-here-change-in-production"]
)
def test_reject_weak_configuration(value):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(jwt_secret_key=value)


def test_secret_and_password_repr_redaction():
    settings = get_settings()
    assert settings.jwt_secret_key not in repr(settings)
    request = UserRegisterRequest(
        email="user@example.com",
        username="user",
        full_name="Test",
        password="private-password",
    )
    assert "private-password" not in repr(request)


async def test_registration_really_commits_and_logout_persists(test_engine):
    # No test session override: exercise the real request lifecycle and a second connection.
    assert not app.dependency_overrides
    created_id = None
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response, data = await register(client)
            assert response.status_code == 201
            created_id = response.json()["id"]
            async with test_engine.connect() as connection:
                assert (
                    await connection.scalar(
                        select(User.email).where(User.id == created_id)
                    )
                    == data["email"]
                )
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": data["email"], "password": data["password"]},
            )
            token = login.json()["access_token"]
            assert (
                await client.post(
                    "/api/v1/auth/logout-all",
                    headers={"Authorization": f"Bearer {token}"},
                )
            ).status_code == 204
            async with test_engine.connect() as connection:
                assert (
                    await connection.scalar(
                        select(User.auth_version).where(User.id == created_id)
                    )
                    == 2
                )
            assert (
                await client.get(
                    "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
                )
            ).status_code == 401
    finally:
        if created_id:
            async with test_engine.begin() as connection:
                await connection.execute(
                    delete(AuthSession).where(AuthSession.user_id == created_id)
                )
                await connection.execute(delete(User).where(User.id == created_id))
