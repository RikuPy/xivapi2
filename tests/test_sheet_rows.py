from xivapi2 import XivApiClient


async def test_sheet_rows(client: XivApiClient):
    rows = [
        r
        async for r in client.sheet_rows(
            "Item", rows=[12056, 20530, 21911], fields=["Name", "Description"], language="en"
        )
    ]
    assert len(rows) == 3
    assert rows[0].row_id == 12056
    assert rows[0].fields["Name"] == "Lesser Panda"
    assert rows[0].fields["Description"]
    assert rows[1].row_id == 20530
    assert rows[1].fields["Name"] == "Bom Boko"
    assert rows[1].fields["Description"]
    assert rows[2].row_id == 21911
    assert rows[2].fields["Name"] == "White Whittret"
    assert rows[2].fields["Description"]


async def test_sheet_rows_with_transients(client: XivApiClient):
    rows = [
        r
        async for r in client.sheet_rows(
            "Companion",
            rows=[141, 103],
            fields=["Singular"],
            transients=["Description", "DescriptionEnhanced"],
        )
    ]
    assert len(rows) == 2
    assert rows[0].row_id == 141
    assert rows[0].fields["Singular"] == "lesser panda"
    assert rows[0].transients["Description"]
    assert rows[0].transients["DescriptionEnhanced"]
    assert rows[1].row_id == 103
    assert rows[1].fields["Singular"] == "panda cub"
    assert rows[1].transients["Description"]
    assert rows[1].transients["DescriptionEnhanced"]


async def test_one_page(client: XivApiClient):
    rows = [r async for r in client.sheet_rows("Item", fields=["Name"], limit=275)]
    assert len(rows) == 275


async def test_multiple_pages(client: XivApiClient):
    rows = [r async for r in client.sheet_rows("Item", fields=["Name"], limit=625)]
    assert len(rows) == 625
