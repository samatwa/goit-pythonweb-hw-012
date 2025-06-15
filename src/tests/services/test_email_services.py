import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.email import send_email


@pytest.mark.asyncio
@patch("src.services.email.FastMail")
@patch("src.services.email.create_email_token", return_value="fake-token")
async def test_send_email_success(mock_token, mock_fastmail):
    """
    Тестує успішну відправку електронного листа.
    """
    # Arrange
    mock_instance = MagicMock()
    mock_instance.send_message = AsyncMock()  
    mock_fastmail.return_value = mock_instance

    # Act
    await send_email(
        email="test@example.com", username="testuser", host="http://localhost:8000"
    )

    # Assert
    mock_token.assert_called_once_with("test@example.com")
    mock_instance.send_message.assert_awaited_once()
    args, kwargs = mock_instance.send_message.call_args
    assert kwargs["template_name"] == "verify_email.html"
