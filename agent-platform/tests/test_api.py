"""
API endpoint tests. These use FastAPI's dependency override system to
replace the real database session and the real agent graph with
lightweight fakes, so the tests run fast, free, and without needing a
live OpenAI key or PostgreSQL instance — they're testing the API
contract (request/response shape, status codes), not the LLM itself.

For a true end-to-end run against the real graph and a real database,
start the app normally (see README) and hit these same endpoints with
curl or the Swagger UI at /docs.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.database.session import get_session


class _FakeSession:
    """Minimal stand-in for an AsyncSession — just enough for the routes
    under test to call .add() / .commit() / .execute() without error."""

    def add(self, obj):
        pass

    async def commit(self):
        pass

    async def execute(self, *args, **kwargs):
        class _EmptyResult:
            def scalars(self):
                class _Scalars:
                    def all(self):
                        return []
                return _Scalars()
        return _EmptyResult()


async def _override_get_session():
    yield _FakeSession()


app.dependency_overrides[get_session] = _override_get_session


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_history_endpoint_returns_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/history")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_chat_endpoint_rejects_missing_question():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={})
    assert response.status_code == 422  # Pydantic validation error, no question field
