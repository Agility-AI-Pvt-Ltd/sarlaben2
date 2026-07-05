from abc import ABC, abstractmethod


class BaseSTT(ABC):
    @abstractmethod
    async def transcribe(self, audio: bytes) -> str:
        raise NotImplementedError
