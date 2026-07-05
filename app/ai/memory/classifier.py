from app.core.constants import CattleMemoryType


class MemoryClassifier:
    def classify(self, text: str) -> CattleMemoryType:
        lowered = text.lower()
        if any(
            word in lowered for word in ("fever", "sick", "health", "vet", "injury")
        ):
            return CattleMemoryType.MEDICAL
        if any(word in lowered for word in ("feed", "fodder", "water", "grass")):
            return CattleMemoryType.FEEDING
        if any(word in lowered for word in ("milk", "yield", "litre", "liter")):
            return CattleMemoryType.MILK
        if any(word in lowered for word in ("medicine", "vaccine", "dose")):
            return CattleMemoryType.MEDICINE
        return CattleMemoryType.GENERAL
