import asyncio
import base64
import json
from urllib import error, request

from app.ai.speech.tts.base import BaseTTS
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"


class SarvamTTS(BaseTTS):
    async def synthesize(self, text: str) -> bytes:
        if not text.strip():
            return b""
        if not settings.sarvam_api_key:
            raise ServiceUnavailableError("SARVAM_API_KEY is not configured")

        payload = json.dumps(
            {
                "text": text[:2500],
                "target_language_code": "hi-IN",
                "model": "bulbul:v3",
                "speaker": "shubh",
                "pace": 1,
                "output_audio_codec": "mp3",
            }
        ).encode("utf-8")
        http_request = request.Request(
            SARVAM_TTS_URL,
            data=payload,
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            response_payload = await asyncio.to_thread(self._send_request, http_request)
        except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
            raise ServiceUnavailableError("Sarvam text-to-speech failed") from exc

        audio_chunks = response_payload.get("audios") or []
        if not audio_chunks:
            raise ServiceUnavailableError("Sarvam text-to-speech returned no audio")
        return base64.b64decode("".join(audio_chunks))

    def _send_request(self, http_request: request.Request) -> dict:
        with request.urlopen(http_request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
