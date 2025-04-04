import io

from PIL import Image


async def test_get_map(client):
    map_bytes = await client.get_map("s1d1", "00")
    assert map_bytes
    map_image = Image.open(io.BytesIO(map_bytes))
    assert map_image.format == "JPEG"
