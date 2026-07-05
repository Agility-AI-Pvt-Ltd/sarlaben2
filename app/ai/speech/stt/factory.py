from app.ai.speech.stt.base import BaseSTT
from app.ai.speech.stt.sarvam_stt import SarvamSTT


class STTFactory:
    @staticmethod
    def create() -> BaseSTT:
        return SarvamSTT()
