from app.ai.memory.extractor import MemoryExtractor


class MemoryService:
    def __init__(self) -> None:
        self.extractor = MemoryExtractor()

    def extract_memories(self, text: str):
        return self.extractor.extract(text)
