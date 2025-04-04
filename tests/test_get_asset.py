import io

from PIL import Image

from xivapi2 import XivApiClient


async def test_get_asset(client: XivApiClient):
    png = await client.get_asset("ui/icon/059000/059534.tex", "png")
    assert png
    image = Image.open(io.BytesIO(png))
    assert image.format == "PNG"
    jpeg = await client.get_asset("ui/icon/059000/059534.tex", "jpg")
    assert jpeg
    image = Image.open(io.BytesIO(jpeg))
    assert image.format == "JPEG"
