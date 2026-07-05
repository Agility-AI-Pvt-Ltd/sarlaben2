from dataclasses import dataclass

from app.ai.memory.classifier import MemoryClassifier


@dataclass(frozen=True)
class ExtractedMemory:
    text: str
    memory_type: str
    confidence: float


class MemoryExtractor:
    def __init__(self) -> None:
        self.classifier = MemoryClassifier()

    def extract(self, text: str) -> list[ExtractedMemory]:
        cleaned = text.strip()
        if not cleaned:
            return []
        memory_type = self.classifier.classify(cleaned)
        return [
            ExtractedMemory(text=cleaned, memory_type=memory_type.value, confidence=0.5)
        ]
