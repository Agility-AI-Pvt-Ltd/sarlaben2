from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services.twilio_verify_service import TwilioVerifyService


class FakeCreateResource:
    def __init__(self, status: str) -> None:
        self.status = status
        self.calls: list[dict[str, str]] = []

    def create(self, **kwargs: str) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(status=self.status)


class FakeVerifyService:
    def __init__(self) -> None:
        self.verifications = FakeCreateResource("pending")
        self.verification_checks = FakeCreateResource("approved")


class FakeServices:
    def __init__(self, service: FakeVerifyService) -> None:
        self.service = service
        self.service_sids: list[str] = []

    def __call__(self, service_sid: str) -> FakeVerifyService:
        self.service_sids.append(service_sid)
        return self.service


@pytest.mark.asyncio
async def test_twilio_verify_sends_and_approves_sms_otp() -> None:
    twilio_service = FakeVerifyService()
    services = FakeServices(twilio_service)
    client = SimpleNamespace(
        verify=SimpleNamespace(v2=SimpleNamespace(services=services))
    )
    config = Settings(
        _env_file=None,
        TWILIO_ACCOUNT_SID="test-account",
        TWILIO_AUTH_TOKEN="test-token",
        TWILIO_VERIFY_SERVICE_SID="test-service",
    )
    verifier = TwilioVerifyService(
        client=client,  # type: ignore[arg-type]
        config=config,
    )

    send_status = await verifier.send_otp("+919876543210")
    approved = await verifier.verify_otp("+919876543210", "123456")

    assert send_status == "pending"
    assert approved is True
    assert services.service_sids == ["test-service", "test-service"]
    assert twilio_service.verifications.calls == [
        {"to": "+919876543210", "channel": "sms"}
    ]
    assert twilio_service.verification_checks.calls == [
        {"to": "+919876543210", "code": "123456"}
    ]
