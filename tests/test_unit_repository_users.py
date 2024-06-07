import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar_url
)
from src.schemas.users import UserSchema


@pytest.mark.asyncio
async def test_get_user_by_email():
    email = "test@example.com"
    user = User(email=email)

    session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=user)
    session.execute = AsyncMock(return_value=mock_result)

    result = await get_user_by_email(email, session)
    result = await result  # добавляем await для корутины
    assert result == user


@pytest.mark.asyncio
async def test_create_user():
    user_data = UserSchema(email="test@example.com", username="testuser", password="testpwd")
    user = User(email=user_data.email)

    session = MagicMock(spec=AsyncSession)
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    with patch("src.repository.users.Gravatar") as MockGravatar:
        mock_gravatar = MockGravatar.return_value
        mock_gravatar.get_image.return_value = "http://example.com/avatar.png"
        result = await create_user(user_data, session)
        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()
        assert result.email == user.email
        assert result.avatar == "http://example.com/avatar.png"


@pytest.mark.asyncio
async def test_update_token():
    user = User(email="test@example.com")
    token = "new_token"

    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()

    await update_token(user, token, session)
    assert user.refresh_token == token
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_confirmed_email():
    email = "test@example.com"
    user = User(email=email)

    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()

    with patch("src.repository.users.get_user_by_email", AsyncMock(return_value=user)):
        await confirmed_email(email, session)
        assert user.confirmed
        session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_avatar_url():
    email = "test@example.com"
    url = "http://example.com/avatar.png"
    user = User(email=email)

    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    with patch("src.repository.users.get_user_by_email", AsyncMock(return_value=user)):
        result = await update_avatar_url(email, url, session)
        assert user.avatar == url
        session.commit.assert_called_once()
        session.refresh.assert_called_once()
        assert result == user
