"""Tests for `schemas` package."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from schemas.user import (  # type: ignore
    UserBase,
    UserCreate,
    UserSchema,
    UserUpdate,
    UserUpdatePassword,
    UserResponse,
    UserPublic,
)
from schemas.auth import (  # type: ignore
    Token,
    TokenRefreshRequest,
    TokenRefreshResponse,
    SignInRequest,
    SignInResponse,
    SignUpRequest,
    SignUpResponse,
)
from schemas.chat import (  # type: ignore
    BaseChat,
    ChatCreate,
    ChatUpdate,
    SetTitleRequest,
    ChatSchema,
    ChatResponse,
)
from schemas.message import (  # type: ignore
    BaseMessage,
    MessageCreate,
    MessageUpdate,
    MessageSchema,
    MessageResponse,
)
from schemas.base import OperationResponse  # type: ignore
from schemas.ai import (  # type: ignore
    AssistantMessage,
    UserMessage,
    ProviderResponse,
    ProviderResponseStream,
    ProviderResponseChunk,
    ProviderInfo,
    ProviderStatus,
    GenerateRequest,
    SetProviderRequest,
    SetModelRequest,
    ProviderSwitchRequest,
    AIServiceStatusResponse,
    ProviderListResponse,
    ProviderDetailResponse,
    ModelListResponse,
)

NOW = datetime.now(timezone.utc)


def user_orm_like(**overrides):
    data = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "settings": {},
        "balance": 0.0,
        "api_key": None,
        "refresh_token": None,
        "refresh_token_expires_at": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return data


class TestUserSchemas:
    def test_user_create_ok(self):
        u = UserCreate(username="validname", email="a@b.c", password="password1")
        assert u.username == "validname"

    def test_user_create_short_username(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", email="a@b.c", password="password1")

    def test_user_create_short_password(self):
        with pytest.raises(ValidationError):
            UserCreate(username="validname", email="a@b.c", password="short")

    def test_user_create_bad_email(self):
        with pytest.raises(ValidationError):
            UserCreate(username="validname", email="not-an-email", password="password1")

    def test_user_schema_from_attributes(self):
        u = UserSchema.model_validate(user_orm_like())
        assert u.id == 1
        assert u.balance == 0.0

    def test_user_update_extra_forbid(self):
        with pytest.raises(ValidationError):
            UserUpdate(username="abc", unknown_field="x")

    def test_user_update_ok(self):
        u = UserUpdate(username="newname", balance=5.0)
        assert u.username == "newname"
        assert u.balance == 5.0

    def test_user_update_negative_balance(self):
        with pytest.raises(ValidationError):
            UserUpdate(balance=-1.0)

    def test_user_update_password(self):
        p = UserUpdatePassword(current_password="password1", new_password="password2")
        assert p.new_password == "password2"
        with pytest.raises(ValidationError):
            UserUpdatePassword(current_password="short", new_password="password2")

    def test_user_response(self):
        resp = UserResponse.model_validate(user_orm_like())
        assert resp.email == "test@example.com"

    def test_user_public(self):
        p = UserPublic(id=1, username="testuser")
        assert p.username == "testuser"


class TestAuthSchemas:
    def test_token(self):
        t = Token(
            access_token="a",
            refresh_token="r",
            access_token_expires_in=60,
            refresh_token_expires_in=3600,
        )
        assert t.token_type == "bearer"

    def test_refresh_request(self):
        r = TokenRefreshRequest(refresh_token="tok")
        assert r.refresh_token == "tok"

    def test_sign_in_request(self):
        r = SignInRequest(email="a@b.c", password="password1")
        assert r.email == "a@b.c"
        with pytest.raises(ValidationError):
            SignInRequest(email="a@b.c", password="bad")

    def test_sign_up_is_user_create(self):
        r = SignUpRequest(username="validname", email="a@b.c", password="password1")
        assert r.username == "validname"


class TestChatSchemas:
    def test_base_chat_defaults(self):
        c = BaseChat()
        assert c.title == "New chat"
        assert c.model == "gpt-4o-mini"
        assert c.provider == "openai"

    def test_chat_create_requires_user(self):
        with pytest.raises(ValidationError):
            ChatCreate()

    def test_chat_update_extra_forbid(self):
        with pytest.raises(ValidationError):
            ChatUpdate(bad_field=1)

    def test_chat_update_temperature_bounds(self):
        with pytest.raises(ValidationError):
            ChatUpdate(temperature=3.0)
        with pytest.raises(ValidationError):
            ChatUpdate(max_tokens=0)

    def test_chat_update_ok(self):
        u = ChatUpdate(title="New", pinned=True, temperature=0.9)
        assert u.pinned is True

    def test_set_title(self):
        t = SetTitleRequest(title="Abc")
        assert t.title == "Abc"
        with pytest.raises(ValidationError):
            SetTitleRequest(title="")

    def test_chat_response(self):
        c = ChatResponse.model_validate(
            {
                "id": 1,
                "user_id": 2,
                "title": "Hi",
                "model": "gpt-4",
                "provider": "openai",
                "position": 1,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        assert c.position == 1
        assert c.pinned is False


class TestMessageSchemas:
    def test_base_message(self):
        m = BaseMessage(role="user", content="hello")
        assert m.prompt_tokens == 0

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            BaseMessage(role="admin", content="hello")

    def test_empty_content(self):
        with pytest.raises(ValidationError):
            BaseMessage(role="user", content="")

    def test_message_create(self):
        m = MessageCreate(role="assistant", content="resp", chat_id=1)
        assert m.chat_id == 1

    def test_message_update_extra_forbid(self):
        with pytest.raises(ValidationError):
            MessageUpdate(role="user")

    def test_message_response(self):
        m = MessageResponse.model_validate(
            {
                "id": 5,
                "chat_id": 1,
                "role": "user",
                "content": "hi",
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        assert m.id == 5


class TestBaseSchemas:
    def test_operation_response(self):
        o = OperationResponse(
            success=True,
            message="ok",
            previous_value="a",
            new_value="b",
        )
        assert o.new_value == "b"


class TestAISchemas:
    def test_assistant_message(self):
        m = AssistantMessage(content="x")
        assert m.role == "assistant"

    def test_user_message_invalid_role(self):
        with pytest.raises(ValidationError):
            UserMessage(role="assistant", content="x")

    def test_provider_response(self):
        r = ProviderResponse()
        assert r.model == "gpt-4o-mini"
        assert r.message.content == ""

    def test_provider_response_stream(self):
        assert issubclass(ProviderResponseStream, ProviderResponse)

    def test_provider_chunk(self):
        c = ProviderResponseChunk(content="abc")
        assert c.content == "abc"

    def test_provider_info(self):
        info = ProviderInfo(
            name="openai",
            prefix="openai/v1",
            supported_models=["gpt-4"],
            current_model="gpt-4",
        )
        assert info.name == "openai"

    def test_provider_status(self):
        status = ProviderStatus(
            current_provider="openai",
            current_model="gpt-4",
            available_providers=["openai"],
            registered_providers=["openai"],
        )
        assert status.current_provider == "openai"

    def test_generate_request_empty_prompt(self):
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="")

    def test_generate_request_temperature_bounds(self):
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="x", temperature=0.0)
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="x", temperature=2.5)

    def test_set_provider_request(self):
        r = SetProviderRequest(provider="openai")
        assert r.provider == "openai"
        with pytest.raises(ValidationError):
            SetProviderRequest()

    def test_set_model_request(self):
        r = SetModelRequest(model="gpt-4")
        assert r.model == "gpt-4"
        with pytest.raises(ValidationError):
            SetModelRequest()

    def test_provider_switch_request(self):
        r = ProviderSwitchRequest(provider="openai")
        assert r.model is None

    def test_ai_status_response(self):
        r = AIServiceStatusResponse(
            current_provider="openai",
            current_model="gpt-4",
            available_providers=["openai"],
            registered_providers=["openai"],
            is_configured=True,
        )
        assert r.is_configured is True

    def test_provider_list_response(self):
        r = ProviderListResponse(providers=["openai"], current_provider="openai")
        assert r.providers == ["openai"]

    def test_provider_detail_response(self):
        info = ProviderInfo(
            name="openai",
            prefix="openai/v1",
            supported_models=["gpt-4"],
            current_model="gpt-4",
        )
        r = ProviderDetailResponse(provider=info, is_current=True)
        assert r.is_current is True

    def test_model_list_response(self):
        r = ModelListResponse(
            provider="openai", models=["gpt-4"], current_model="gpt-4"
        )
        assert r.current_model == "gpt-4"
