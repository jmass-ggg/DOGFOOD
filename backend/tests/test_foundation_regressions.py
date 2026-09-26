"""Behavior checks for foundation boundaries that scaffold tests missed."""

import json
import logging
from io import StringIO

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.config import Settings
from app.core.database import get_db_session
from app.core.logging import JSONLogFormatter, RequestIDFilter
from app.main import create_app


def test_invalid_database_url_does_not_echo_credentials():
    with pytest.raises(ValidationError) as error:
        Settings(database_url="postgresql+asyncpg://secret:password@localhost/testdb")
    assert "password" not in str(error.value)
    assert "secret" not in str(error.value)


@pytest.mark.asyncio
async def test_session_dependency_never_commits_implicitly(monkeypatch):
    class Session:
        committed = False
        closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            self.closed = True

        async def commit(self):
            self.committed = True

    session = Session()
    monkeypatch.setattr("app.core.database.session_factory", lambda: session)
    dependency = get_db_session()
    assert await anext(dependency) is session
    with pytest.raises(StopAsyncIteration):
        await anext(dependency)
    assert session.closed
    assert not session.committed


@pytest.mark.asyncio
async def test_unhandled_error_keeps_request_id_in_response():
    app = create_app()

    @app.get("/failure")
    async def failure():
        raise RuntimeError("private password")

    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
        response = await client.get("/failure", headers={"X-Request-ID": "failure-123"})
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "failure-123"
    assert response.json()["request_id"] == "failure-123"
    assert "password" not in response.text


@pytest.mark.asyncio
async def test_http_and_validation_errors_use_error_envelope():
    app = create_app()

    @app.get("/number/{value}")
    async def number(value: int):
        return {"value": value}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        missing = await client.get("/missing")
        invalid = await client.get("/number/private-password")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "HTTP_ERROR"
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "private-password" not in invalid.text


@pytest.mark.asyncio
async def test_request_log_is_json_without_query_string():
    app = create_app()
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(RequestIDFilter())
    handler.setFormatter(JSONLogFormatter())
    logger = logging.getLogger("dogfood.request")
    original_handlers = logger.handlers[:]
    logger.handlers = [handler]
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/missing?token=private-password", headers={"X-Request-ID": "trace-123"})
    finally:
        logger.handlers = original_handlers
    entry = json.loads(stream.getvalue().strip())
    assert entry["request_id"] == "trace-123"
    assert entry["method"] == "GET"
    assert entry["path"] == "<unmatched>"
    assert entry["status_code"] == 404
    assert entry["duration_ms"] >= 0
    assert entry["timestamp"].endswith("+00:00")
    assert "private-password" not in stream.getvalue()
