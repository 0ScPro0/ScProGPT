"""API integration tests for FastAPI endpoints."""

from types import SimpleNamespace

import pytest

from schemas.ai import (  # type: ignore
    ProviderResponse,
    ProviderResponseStream,
    ProviderResponseChunk,
    AssistantMessage,
)

SIGNUP_DATA = {
    "username": "apitest",
    "email": "apitest@example.com",
    "password": "password123",
}


async def signup(client, data=None):
    payload = data or SIGNUP_DATA
    resp = await client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# Root & app
# ============================================================


class TestRoot:
    async def test_root(self, client):
        resp = await client.get("/api/v1/")
        assert resp.status_code == 200
        assert "message" in resp.json()

    async def test_api_docs(self, client):
        resp = await client.get("/api/v1/docs")
        assert resp.status_code in (200, 307)


# ============================================================
# Auth endpoints
# ============================================================


class TestAuthEndpoints:
    async def test_signup(self, client):
        body = await signup(client)
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["user"]["email"] == SIGNUP_DATA["email"]

    async def test_signup_duplicate(self, client):
        await signup(client)
        resp = await client.post("/api/v1/auth/signup", json=SIGNUP_DATA)
        assert resp.status_code == 403

    async def test_signin(self, client):
        await signup(client)
        resp = await client.post(
            "/api/v1/auth/signin",
            json={"email": SIGNUP_DATA["email"], "password": SIGNUP_DATA["password"]},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    async def test_signin_wrong_password(self, client):
        await signup(client)
        resp = await client.post(
            "/api/v1/auth/signin",
            json={"email": SIGNUP_DATA["email"], "password": "wrongpass1"},
        )
        assert resp.status_code == 403

    async def test_refresh(self, client):
        body = await signup(client)
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": body["refresh_token"]},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    async def test_refresh_invalid(self, client):
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "bad-token"}
        )
        assert resp.status_code == 403

    async def test_logout(self, client):
        body = await signup(client)
        resp = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Successfully logged out"

    async def test_logout_unauthenticated(self, client):
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code in (401, 403)


# ============================================================
# Users endpoints
# ============================================================


class TestUsersEndpoints:
    async def test_get_me(self, client):
        body = await signup(client)
        resp = await client.get(
            "/api/v1/users/me", headers=auth_headers(body["access_token"])
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == SIGNUP_DATA["username"]

    async def test_get_me_no_auth(self, client):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code in (401, 403)

    async def test_get_all_users_denied_for_user(self, client):
        body = await signup(client)
        resp = await client.get(
            "/api/v1/users/", headers=auth_headers(body["access_token"])
        )
        assert resp.status_code == 403

    async def test_get_all_users_superuser(self, client):
        body = await signup(
            client,
            {
                "username": "admin",
                "email": "admin2@example.com",
                "password": "password123",
            },
        )
        # promote user to superuser directly
        from repositories.user import user_repository  # type: ignore
        from api.dependencies import get_db_session  # type: ignore

        async for session in get_db_session():
            await user_repository.update_field(
                session=session,
                object_id=body["user"]["id"],
                field_name="is_superuser",
                field_value=True,
            )
        resp = await client.get(
            "/api/v1/users/", headers=auth_headers(body["access_token"])
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_user_by_id_superuser(self, client):
        body = await signup(client)
        target = await signup(
            client,
            {
                "username": "target",
                "email": "target@example.com",
                "password": "password123",
            },
        )
        from repositories.user import user_repository  # type: ignore
        from api.dependencies import get_db_session  # type: ignore

        async for session in get_db_session():
            await user_repository.update_field(
                session=session,
                object_id=body["user"]["id"],
                field_name="is_superuser",
                field_value=True,
            )
        resp = await client.get(
            f"/api/v1/users/{target['user']['id']}",
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200


# ============================================================
# Chats endpoints
# ============================================================


class TestChatsEndpoints:
    async def test_create_chat(self, client):
        body = await signup(client)
        resp = await client.post(
            "/api/v1/chats/",
            json={"title": "My chat", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "My chat"
        assert data["user_id"] == body["user"]["id"]

    async def test_get_user_chats(self, client):
        body = await signup(client)
        await client.post(
            "/api/v1/chats/",
            json={"title": "c1", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        resp = await client.get(
            "/api/v1/chats/me", headers=auth_headers(body["access_token"])
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_chat_by_id(self, client):
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "single", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.get(
            f"/api/v1/chats/{chat_id}",
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == chat_id

    async def test_update_chat_title(self, client):
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "old", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.patch(
            f"/api/v1/chats/{chat_id}/title",
            json={"title": "new title"},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["new_value"] == "new title"

    async def test_update_chat_provider(self, client):
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "p", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.patch(
            f"/api/v1/chats/{chat_id}/provider",
            json={"provider": "openrouter"},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_update_chat_model(self, client):
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "m", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        model = created.json()["model"]
        resp = await client.patch(
            f"/api/v1/chats/{chat_id}/model",
            json={"model": model},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200

    async def test_get_provider_status(self, client):
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "status", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.get(
            f"/api/v1/chats/{chat_id}/status",
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["current_provider"] == "openai"

    async def test_delete_chat(self, client):
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "del", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.delete(
            f"/api/v1/chats/{chat_id}",
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200

    async def test_foreign_chat_denied(self, client):
        owner = await signup(client)
        attacker = await signup(
            client,
            {
                "username": "attacker",
                "email": "attacker@example.com",
                "password": "password123",
            },
        )
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "private", "user_id": owner["user"]["id"]},
            headers=auth_headers(owner["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.patch(
            f"/api/v1/chats/{chat_id}/title",
            json={"title": "hacked"},
            headers=auth_headers(attacker["access_token"]),
        )
        assert resp.status_code == 403

    async def test_chats_unauthenticated(self, client):
        resp = await client.get("/api/v1/chats/me")
        assert resp.status_code in (401, 403)


# ============================================================
# Messages endpoints
# ============================================================


class FakeAIService:
    """Stub for AIService used by message text endpoints."""

    def __init__(self, *args, **kwargs):
        pass

    async def generate_text(self, **kwargs):
        return ProviderResponse(
            provider="openai",
            model="gpt-4",
            message=AssistantMessage(content="AI response"),
            usage={"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            cost=0.01,
        )

    async def generate_stream(self, **kwargs):
        yield ProviderResponseChunk(content="Hi")
        yield ProviderResponseStream(
            provider="openai",
            model="gpt-4",
            message=AssistantMessage(content="Hi"),
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            cost=0.01,
        )


class FailingAIServiceError(FakeAIService):
    """AIService stub that raises AIServiceError."""

    async def generate_text(self, **kwargs):
        from core.exceptions import AIServiceError  # type: ignore

        raise AIServiceError("upstream failed")

    async def generate_stream(self, **kwargs):
        from core.exceptions import AIServiceError  # type: ignore

        raise AIServiceError("upstream failed")
        yield  # pragma: no cover


class FailingAIServiceCrash(FakeAIService):
    """AIService stub that raises an unexpected exception."""

    async def generate_stream(self, **kwargs):
        raise RuntimeError("boom")
        yield  # pragma: no cover


@pytest.fixture
def override_ai(monkeypatch):
    """Patch AIService used by API dependency with a fake."""

    def _patch(app, service_cls=FakeAIService):
        from api.dependencies import get_ai_service  # type: ignore

        app.dependency_overrides[get_ai_service] = lambda: service_cls()

    return _patch


class TestMessagesEndpoints:
    async def test_get_chat_messages(self, client):
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "mchat", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.get(
            f"/api/v1/chats/{chat_id}/messages/",
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_messages_foreign_chat(self, client):
        owner = await signup(client)
        attacker = await signup(
            client,
            {
                "username": "atk2",
                "email": "atk2@example.com",
                "password": "password123",
            },
        )
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "private", "user_id": owner["user"]["id"]},
            headers=auth_headers(owner["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.get(
            f"/api/v1/chats/{chat_id}/messages/",
            headers=auth_headers(attacker["access_token"]),
        )
        assert resp.status_code in (403, 404)

    async def test_create_assistant_message(self, client, override_ai):
        from main import app  # type: ignore

        override_ai(app)
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "gen", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.post(
            f"/api/v1/chats/{chat_id}/messages/text",
            json={"prompt": "Hello AI"},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "assistant"
        assert resp.json()["content"] == "AI response"

    async def test_create_assistant_message_stream(self, client, override_ai):
        from main import app  # type: ignore

        override_ai(app)
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "stream", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.post(
            f"/api/v1/chats/{chat_id}/messages/text/stream",
            json={"prompt": "Hi"},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert "AI response" not in resp.text

    async def test_create_assistant_message_ai_error(self, client, override_ai):
        from main import app  # type: ignore

        override_ai(app, FailingAIServiceError)
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "errt", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.post(
            f"/api/v1/chats/{chat_id}/messages/text",
            json={"prompt": "Hi"},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 502
        assert "upstream failed" in resp.text

    async def test_stream_ai_error(self, client, override_ai):
        from main import app  # type: ignore

        override_ai(app, FailingAIServiceError)
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "errs", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.post(
            f"/api/v1/chats/{chat_id}/messages/text/stream",
            json={"prompt": "Hi"},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert "upstream failed" in resp.text

    async def test_stream_crash(self, client, override_ai):
        from main import app  # type: ignore

        override_ai(app, FailingAIServiceCrash)
        body = await signup(client)
        created = await client.post(
            "/api/v1/chats/",
            json={"title": "crash", "user_id": body["user"]["id"]},
            headers=auth_headers(body["access_token"]),
        )
        chat_id = created.json()["id"]
        resp = await client.post(
            f"/api/v1/chats/{chat_id}/messages/text/stream",
            json={"prompt": "Hi"},
            headers=auth_headers(body["access_token"]),
        )
        assert resp.status_code == 200
        assert "boom" in resp.text
