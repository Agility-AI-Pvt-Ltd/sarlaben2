import pytest
from pydantic import ValidationError

from app.schemas.user import OTPRequest, OTPVerifyRequest, UserUpdate


def test_otp_request_requires_e164_phone_number() -> None:
    request = OTPRequest(phone_number=" +919876543210 ")

    assert request.phone_number == "+919876543210"

    with pytest.raises(ValidationError):
        OTPRequest(phone_number="9876543210")


def test_otp_code_requires_four_to_ten_digits() -> None:
    request = OTPVerifyRequest(
        phone_number="+919876543210",
        code="123456",
    )

    assert request.code == "123456"

    with pytest.raises(ValidationError):
        OTPVerifyRequest(phone_number="+919876543210", code="12ab")


def test_user_update_cleans_profile_fields() -> None:
    request = UserUpdate(
        full_name="  Ravi Kumar  ",
        profile_image_uri="  file:///tmp/profile.jpg  ",
    )

    assert request.full_name == "Ravi Kumar"
    assert request.profile_image_uri == "file:///tmp/profile.jpg"


def test_user_update_accepts_only_supported_languages() -> None:
    assert UserUpdate(preferred_language="en-IN").preferred_language == "en-IN"
    assert UserUpdate(preferred_language="hi-IN").preferred_language == "hi-IN"

    with pytest.raises(ValidationError):
        UserUpdate(preferred_language="ta-IN")
