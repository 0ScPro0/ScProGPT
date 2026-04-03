"""
Integration tests for AuthService.

Tests cover the full auth cycle:
- Signup
- Signin
- Token refresh
- Logout
- Auth errors
"""

import pytest
import pytest_asyncio

from core.exceptions import AuthError  # type: ignore
from core.security import decode_token, hash_password, verify_password  # type: ignore
from schemas.auth import SignUpRequest, SignInRequest  # type: ignore


# ============================================================
# TESTS: Signup
# ============================================================


class TestAuthSignup:
    """User registration tests."""

    @pytest.mark.asyncio
    async def test_signup_success(self, auth_service, signup_request_factory):
        """Successful registration of a new user."""
        request = signup_request_factory()

        response = await auth_service.signup(request)

        # Check response
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.user.email == request.email
        assert response.user.username == request.username
        assert response.access_token_expires_in is not None
        assert response.refresh_token_expires_in is not None

    @pytest.mark.asyncio
    async def test_signup_creates_user_in_db(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Signup creates a user in DB."""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user is not None
        assert user.email == request.email

    @pytest.mark.asyncio
    async def test_signup_password_is_hashed(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Password is saved in hashed form."""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.password_hash != request.password
        assert verify_password(request.password, user.password_hash)

    @pytest.mark.asyncio
    async def test_signup_user_is_active_by_default(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Registered user is active."""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_signup_user_is_not_superuser(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Registered user is not a superuser."""
        request = signup_request_factory()

        await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.is_superuser is False

    @pytest.mark.asyncio
    async def test_signup_duplicate_email_raises_error(
        self, auth_service, signup_request_factory, test_user_in_db
    ):
        """Signup with existing email raises error."""
        request = signup_request_factory(email=test_user_in_db.email)

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signup(request)

        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_signup_returns_jwt_tokens_with_correct_user_id(
        self, auth_service, signup_request_factory
    ):
        """Tokens contain correct user_id."""
        request = signup_request_factory()

        response = await auth_service.signup(request)

        access_payload = decode_token(response.access_token)
        refresh_payload = decode_token(response.refresh_token)

        assert access_payload["sub"] == response.user.id
        assert refresh_payload["sub"] == response.user.id

    @pytest.mark.asyncio
    async def test_signup_stores_refresh_token_in_db(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Refresh token is saved in DB."""
        request = signup_request_factory()

        response = await auth_service.signup(request)

        user = await user_crud.get_by_email(test_session, request.email)
        assert user.refresh_token == response.refresh_token
        assert user.refresh_token_expires_at is not None


# ============================================================
# TESTS: Signin
# ============================================================


class TestAuthSignin:
    """User signin tests."""

    @pytest.mark.asyncio
    async def test_signin_success(self, auth_service, test_user_in_db):
        """Successful signin with correct credentials."""
        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",  # password from fixture
        )

        response = await auth_service.signin(request)

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.user.id == test_user_in_db.id
        assert response.user.email == test_user_in_db.email

    @pytest.mark.asyncio
    async def test_signin_wrong_password_raises_error(
        self, auth_service, test_user_in_db
    ):
        """Signin with wrong password raises error."""
        request = SignInRequest(
            email=test_user_in_db.email,
            password="WrongPassword456!",
        )

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signin(request)

        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_signin_nonexistent_email_raises_error(self, auth_service):
        """Signin with non-existent email raises error."""
        request = SignInRequest(
            email="nonexistent@example.com",
            password="SomePassword123!",
        )

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signin(request)

        assert "Invalid credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_signin_deactivated_user_raises_error(
        self, auth_service, test_user_in_db, user_crud, test_session
    ):
        """Signin for deactivated user raises error."""
        # Deactivate user
        await user_crud.deactivate(test_session, user_id=test_user_in_db.id)

        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",
        )

        with pytest.raises(AuthError) as exc_info:
            await auth_service.signin(request)

        assert "deactivated" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_signin_updates_refresh_token_in_db(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Signin updates refresh token in DB."""
        old_token = "old_refresh_token"
        await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token=old_token,
            expires_at=None,
        )

        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",
        )

        response = await auth_service.signin(request)

        user = await user_crud.get(test_session, test_user_in_db.id)
        assert user.refresh_token == response.refresh_token
        assert user.refresh_token != old_token

    @pytest.mark.asyncio
    async def test_signin_returns_tokens_with_correct_type(
        self, auth_service, test_user_in_db
    ):
        """Tokens have correct type (access/refresh)."""
        request = SignInRequest(
            email=test_user_in_db.email,
            password="TestPassword123!",
        )

        response = await auth_service.signin(request)

        access_payload = decode_token(response.access_token)
        refresh_payload = decode_token(response.refresh_token)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


# ============================================================
# TESTS: Token Refresh
# ============================================================


class TestAuthRefresh:
    """Token refresh tests."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Successful access token refresh."""
        from datetime import datetime, timedelta, timezone
        from core.security import create_refresh_token  # type: ignore
        from schemas.auth import TokenRefreshRequest  # type: ignore

        # Create refresh token
        refresh_token = create_refresh_token({"sub": str(test_user_in_db.id)})
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Save to DB
        await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        request = TokenRefreshRequest(refresh_token=refresh_token)
        response = await auth_service.refresh_token(request)

        assert "access_token" in response
        assert "access_token_expires_in" in response

    @pytest.mark.asyncio
    async def test_refresh_with_fake_token_raises_error(self, auth_service):
        """Refresh with fake token raises error."""
        from schemas.auth import TokenRefreshRequest  # type: ignore

        request = TokenRefreshRequest(refresh_token="fake.token.here")

        with pytest.raises(AuthError) as exc_info:
            await auth_service.refresh_token(request)

        assert "Invalid refresh token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_with_wrong_stored_token_raises_error(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Refresh with token not matching DB raises error."""
        from datetime import datetime, timedelta, timezone
        from core.security import create_refresh_token  # type: ignore
        from schemas.auth import TokenRefreshRequest  # type: ignore

        # Create a token
        refresh_token = create_refresh_token({"sub": str(test_user_in_db.id)})
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # But save a different one
        await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token="different_stored_token",
            expires_at=expires_at,
        )

        request = TokenRefreshRequest(refresh_token=refresh_token)

        with pytest.raises(AuthError) as exc_info:
            await auth_service.refresh_token(request)

        assert "Invalid refresh token" in str(exc_info.value.detail)


# ============================================================
# TESTS: Logout
# ============================================================


class TestAuthLogout:
    """User logout tests."""

    @pytest.mark.asyncio
    async def test_logout_clears_refresh_token(
        self, auth_service, test_user_in_db, test_session, user_crud
    ):
        """Logout clears refresh token in DB."""
        from datetime import datetime, timedelta, timezone
        from core.security import create_refresh_token  # type: ignore

        # Set refresh token
        refresh_token = create_refresh_token({"sub": str(test_user_in_db.id)})
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await user_crud.update_refresh_token(
            test_session,
            user_id=test_user_in_db.id,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        # Logout
        result = await auth_service.logout(test_user_in_db.id)

        assert result is True

        # Check that token is cleared
        user = await user_crud.get(test_session, test_user_in_db.id)
        assert user.refresh_token is None
        assert user.refresh_token_expires_at is None

    @pytest.mark.asyncio
    async def test_logout_nonexistent_user(self, auth_service):
        """Logout for non-existent user does not raise error."""
        result = await auth_service.logout(99999)

        assert result is True


# ============================================================
# TESTS: Edge cases
# ============================================================


class TestAuthEdgeCases:
    """Edge cases and additional checks."""

    @pytest.mark.asyncio
    async def test_signup_and_signin_flow(
        self, auth_service, signup_request_factory, test_session, user_crud
    ):
        """Full cycle: signup → signin."""
        # Signup
        signup_request = signup_request_factory()
        signup_response = await auth_service.signup(signup_request)

        assert signup_response.user.email == signup_request.email

        # Signin again
        signin_request = SignInRequest(
            email=signup_request.email,
            password=signup_request.password,
        )
        signin_response = await auth_service.signin(signin_request)

        assert signin_response.user.id == signup_response.user.id

    @pytest.mark.asyncio
    async def test_multiple_signups_with_different_emails(
        self, auth_service, signup_request_factory
    ):
        """Multiple users can be registered."""
        user1 = await auth_service.signup(signup_request_factory())
        user2 = await auth_service.signup(signup_request_factory())

        assert user1.user.id != user2.user.id
        assert user1.user.email != user2.user.email

    @pytest.mark.asyncio
    async def test_signin_returns_same_user_id_as_signup(
        self, auth_service, signup_request_factory
    ):
        """User ID matches between signup and signin."""
        signup_response = await auth_service.signup(signup_request_factory())

        signin_request = SignInRequest(
            email=signup_response.user.email,
            password="TestPassword123!",
        )
        signin_response = await auth_service.signin(signin_request)

        assert signup_response.user.id == signin_response.user.id
