import pytest

from xivapi2 import XivApiClient
from xivapi2.errors import XivApiParameterError, XivApiNotFoundError


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


async def test_400_response(client: XivApiClient):
    with pytest.raises(XivApiParameterError):
        row = await client.get_sheet_row(
            "Item",
            999999999999,
            language="en",
        )


async def test_404_response(client: XivApiClient):
    with pytest.raises(XivApiNotFoundError):
        row = await client.get_sheet_row(
            "Item",
            9999999,
            language="en",
        )