import pytest

from xivapi2 import XivApiClient


async def test_get_row(client: XivApiClient):
    row = await client.get_sheet_row(
        "Item",
        12056,
        language="en",
    )
    assert row["Name"] == "Lesser Panda"
    assert row["Description"]
    assert row["IsUntradable"] is False
    assert row["StackSize"] == 1