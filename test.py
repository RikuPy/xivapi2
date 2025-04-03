import asyncio

from xivapi2 import XivApiClient

client = XivApiClient()
r = asyncio.run(client.get_sheet_row("Item", 12056))
print(r)