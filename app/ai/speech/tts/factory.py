from app.ai.speech.tts.base import BaseTTS
from app.ai.speech.tts.sarvam_tts import SarvamTTS


class TTSFactory:
    @staticmethod
    def create() -> BaseTTS:
        return SarvamTTS()
