from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.call_service import CallService


@pytest.mark.asyncio
async def test_list_for_farmer_delegates_to_repository() -> None:
    farmer_id = uuid4()
    call_logs = [object()]
    service = object.__new__(CallService)
    service.repo = SimpleNamespace(list_for_farmer=AsyncMock(return_value=call_logs))

    result = await service.list_for_farmer(farmer_id)

    assert result is call_logs
    service.repo.list_for_farmer.assert_awaited_once_with(farmer_id)
