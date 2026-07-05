import pytest
from pydantic import ValidationError

from app.schemas.chat import ImageMessageCreate


def test_image_message_accepts_supported_data_url() -> None:
    payload = ImageMessageCreate(
        image_data_url="data:image/jpeg;base64,aGVsbG8gd29ybGQ=",
    )

    assert payload.image_data_url.endswith("aGVsbG8gd29ybGQ=")


def test_image_message_rejects_non_image_data_url() -> None:
    with pytest.raises(ValidationError):
        ImageMessageCreate(
            image_data_url="data:text/plain;base64,aGVsbG8=",
        )
