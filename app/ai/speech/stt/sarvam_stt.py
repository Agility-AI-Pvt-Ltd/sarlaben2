from app.ai.speech.stt.base import BaseSTT


class SarvamSTT(BaseSTT):
    async def transcribe(self, audio: bytes) -> str:
        if not audio:
            return ""
        return "STT placeholder: configure Sarvam API integration."
