import pytest

from xivapi2.client import XivApiClient


@pytest.mark.asyncio
async def test_sheets():
    client = XivApiClient()
    sheets = await client.get_sheets()
    assert sheets
    for sheet in sheets:
        assert isinstance(sheet, str)
