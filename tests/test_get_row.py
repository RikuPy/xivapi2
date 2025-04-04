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


async def test_get_row_with_explicit_fields_and_transients(client: XivApiClient):
    row = await client.get_sheet_row(
        "Companion",
        141,
        language="en",
        fields=["Singular"],
        transients=["Description", "DescriptionEnhanced"],
    )
    assert row.row_id == 141
    assert len(row.fields) == 1
    assert row.fields["Singular"] == "lesser panda"
    assert len(row.transients) == 2
    assert row.transients["Description"]
    assert row.transients["DescriptionEnhanced"]


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