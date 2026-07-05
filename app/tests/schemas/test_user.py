import pytest
from pydantic import ValidationError

from app.schemas.user import OTPRequest, OTPVerifyRequest


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
