from app.ai.speech.tts.base import BaseTTS


class SarvamTTS(BaseTTS):
    async def synthesize(self, text: str) -> bytes:
        return text.encode("utf-8")
