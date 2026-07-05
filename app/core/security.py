from uuid import UUID


def assert_farmer_access(_human_id: UUID, _cattle_id: UUID) -> None:
    """Hook for ownership checks once auth is added."""
