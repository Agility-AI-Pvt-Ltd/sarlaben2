class MemorySummarizer:
    def summarize(self, memories: list[str]) -> str:
        return "\n".join(memory.strip() for memory in memories if memory.strip())
