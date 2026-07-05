from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.cattle import CattleCreate, CattleUpdate
from app.services.cattle_service import CattleService


@pytest.mark.asyncio
async def test_create_cattle_generates_unique_tag_when_missing() -> None:
    created_cattle = object()
    service = object.__new__(CattleService)
    service.cattle_repo = SimpleNamespace(
        get_by_tag=AsyncMock(return_value=None),
        create=AsyncMock(return_value=created_cattle),
    )
    payload = CattleCreate(farmer_id=uuid4(), name="Lakshmi")

    result = await service.create_cattle(payload)

    assert result is created_cattle
    generated_tag = service.cattle_repo.create.await_args.args[0].cattle_tag
    assert generated_tag.startswith("COW-")
    assert len(generated_tag) == 36
    service.cattle_repo.get_by_tag.assert_awaited_once_with(generated_tag)


@pytest.mark.asyncio
async def test_create_cattle_keeps_farmer_provided_id() -> None:
    created_cattle = object()
    service = object.__new__(CattleService)
    service.cattle_repo = SimpleNamespace(
        get_by_tag=AsyncMock(),
        create=AsyncMock(return_value=created_cattle),
    )
    payload = CattleCreate(
        farmer_id=uuid4(),
        name="Lakshmi",
        cattle_id="TN-1042",
    )

    result = await service.create_cattle(payload)

    assert result is created_cattle
    assert service.cattle_repo.create.await_args.args[0].cattle_tag == "TN-1042"
    service.cattle_repo.get_by_tag.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_cattle_deletes_existing_cattle() -> None:
    cattle_id = uuid4()
    cattle = object()
    service = object.__new__(CattleService)
    service.cattle_repo = SimpleNamespace(
        get=AsyncMock(return_value=cattle),
        delete=AsyncMock(),
    )

    await service.delete_cattle(cattle_id)

    service.cattle_repo.get.assert_awaited_once_with(cattle_id)
    service.cattle_repo.delete.assert_awaited_once_with(cattle)


def test_empty_cattle_id_is_treated_as_missing() -> None:
    payload = CattleCreate(farmer_id=uuid4(), name="Lakshmi", cattle_id="  ")

    assert payload.cattle_tag is None


def test_cattle_update_rejects_cattle_tag() -> None:
    with pytest.raises(ValidationError):
        CattleUpdate(cattle_tag="TN-999")
