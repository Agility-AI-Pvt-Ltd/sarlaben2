import asyncio
import logging

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.core.config import Settings, settings
from app.core.exceptions import (
    InvalidVerificationCodeError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class TwilioVerifyService:
    def __init__(
        self,
        client: Client | None = None,
        config: Settings = settings,
    ) -> None:
        self.client = client
        self.config = config

    async def send_otp(self, phone_number: str) -> str:
        try:
            verification = await asyncio.to_thread(
                self._service().verifications.create,
                to=phone_number,
                channel="sms",
            )
        except TwilioRestException as exc:
            logger.exception("Twilio failed to send an OTP")
            raise ServiceUnavailableError("Unable to send a verification code") from exc
        return verification.status

    async def verify_otp(self, phone_number: str, code: str) -> bool:
        try:
            verification = await asyncio.to_thread(
                self._service().verification_checks.create,
                to=phone_number,
                code=code,
            )
        except TwilioRestException as exc:
            if exc.status in {400, 404}:
                raise InvalidVerificationCodeError() from exc
            logger.exception("Twilio failed to check an OTP")
            raise ServiceUnavailableError(
                "Unable to check the verification code"
            ) from exc
        return verification.status == "approved"

    def _service(self):
        if not self.config.twilio_verify_service_sid:
            raise ServiceUnavailableError("TWILIO_VERIFY_SERVICE_SID is not configured")
        return self._get_client().verify.v2.services(
            self.config.twilio_verify_service_sid
        )

    def _get_client(self) -> Client:
        if self.client is not None:
            return self.client
        if not self.config.twilio_account_sid or not self.config.twilio_auth_token:
            raise ServiceUnavailableError("Twilio credentials are not configured")
        self.client = Client(
            self.config.twilio_account_sid,
            self.config.twilio_auth_token,
        )
        return self.client
