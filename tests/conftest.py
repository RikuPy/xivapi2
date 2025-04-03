import pytest

from xivapi2.client import XivApiClient


@pytest.fixture
async def client():
    client = XivApiClient()
    yield client
