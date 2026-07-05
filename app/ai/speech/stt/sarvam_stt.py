import asyncio
import json
from urllib import error, request

from app.ai.speech.stt.base import BaseSTT
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


class SarvamSTT(BaseSTT):
    async def transcribe(self, audio: bytes) -> str:
        if not audio:
            return ""
        if not settings.sarvam_api_key:
            raise ServiceUnavailableError("SARVAM_API_KEY is not configured")

        boundary = "cowx-sarvam-audio-boundary"
        fields = {
            "model": "saaras:v3",
            "mode": "transcribe",
            "language_code": "unknown",
        }
        body = self._multipart_body(boundary, fields, audio)
        http_request = request.Request(
            SARVAM_STT_URL,
            data=body,
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )

        try:
            payload = await asyncio.to_thread(self._send_request, http_request)
        except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
            raise ServiceUnavailableError("Sarvam speech-to-text failed") from exc

        return str(payload.get("transcript") or "").strip()

    def _send_request(self, http_request: request.Request) -> dict:
        with request.urlopen(http_request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))

    def _multipart_body(
        self, boundary: str, fields: dict[str, str], audio: bytes
    ) -> bytes:
        filename, content_type = self._audio_metadata(audio)
        parts: list[bytes] = []
        for key, value in fields.items():
            parts.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                    f"{value}\r\n".encode(),
                ]
            )
        parts.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; name="file"; '
                    f'filename="{filename}"\r\n'
                ).encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                audio,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )
        return b"".join(parts)

    @staticmethod
    def _audio_metadata(audio: bytes) -> tuple[str, str]:
        if audio.startswith(b"RIFF") and audio[8:12] == b"WAVE":
            return "utterance.wav", "audio/wav"
        if audio.startswith(b"\x1aE\xdf\xa3"):
            return "utterance.webm", "audio/webm"
        if audio.startswith(b"OggS"):
            return "utterance.ogg", "audio/ogg"
        if len(audio) >= 8 and audio[4:8] == b"ftyp":
            return "utterance.m4a", "audio/mp4"
        if len(audio) >= 2 and audio[0] == 0xFF and audio[1] & 0xF6 == 0xF0:
            return "utterance.aac", "audio/aac"
        if audio.startswith(b"ID3") or (
            len(audio) >= 2 and audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0
        ):
            return "utterance.mp3", "audio/mpeg"

        return "utterance.m4a", "audio/mp4"
