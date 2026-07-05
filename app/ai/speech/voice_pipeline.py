from app.ai.speech.audio_processor import AudioProcessor
from app.ai.speech.stt.factory import STTFactory
from app.ai.speech.tts.factory import TTSFactory


class VoicePipeline:
    def __init__(self) -> None:
        self.audio_processor = AudioProcessor()
        self.stt = STTFactory.create()
        self.tts = TTSFactory.create()

    async def transcribe(self, audio: bytes) -> str:
        return await self.stt.transcribe(self.audio_processor.normalize_chunk(audio))

    async def synthesize(self, text: str) -> bytes:
        return await self.tts.synthesize(text)
