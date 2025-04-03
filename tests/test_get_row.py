import pytest

from xivapi2 import XivApiClient


async def test_get_row(client: XivApiClient):
    row = await client.get_sheet_row(
        "Item",
        12056,
        language="en",
    )
    assert row.row_id == 12056
    assert row.fields["Name"] == "Lesser Panda"
    assert row.fields["Description"]
    assert row.fields["IsUntradable"] is False
    assert row.fields["StackSize"] == 1