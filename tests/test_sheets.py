from xivapi2.client import XivApiClient


async def test_sheets(client: XivApiClient):
    sheets = await client.sheets()
    assert sheets
    for sheet in sheets:
        assert isinstance(sheet, str)
