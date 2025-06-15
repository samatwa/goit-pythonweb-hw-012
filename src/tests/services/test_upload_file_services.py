import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.upload_file import UploadFileService


@pytest.mark.asyncio
@patch("src.services.upload_file.cloudinary.CloudinaryImage")
@patch("src.services.upload_file.cloudinary.uploader.upload")
async def test_upload_file_success(mock_upload, mock_cloud_image):
    # Arrange
    fake_version = "123456789"
    mock_upload.return_value = {"version": fake_version}

    mock_cloud_image_instance = MagicMock()
    mock_cloud_image_instance.build_url.return_value = (
        "http://res.cloudinary.com/avatar.jpg"
    )
    mock_cloud_image.return_value = mock_cloud_image_instance

    mock_file = AsyncMock()
    mock_file.read.return_value = b"fake image data"

    service = UploadFileService("demo_cloud", "demo_key", "demo_secret")

    # Act
    result = await service.upload_file(mock_file, "testuser")

    # Assert
    mock_file.read.assert_awaited_once()
    mock_upload.assert_called_once()
    mock_cloud_image_instance.build_url.assert_called_once()
    assert result == "http://res.cloudinary.com/avatar.jpg"
