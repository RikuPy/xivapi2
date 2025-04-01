import logging

import aiohttp


class XivApiClient:
    def __init__(self):
        self.base_url = "https://v2.xivapi.com/api"
        self._logger = logging.getLogger()

    async def get_sheets(self):
        resp = await self._request(f"{self.base_url}/sheet")
        return [s["name"] for s in resp["sheets"]]

    async def _request(self, url: str):
        self._logger.debug(f"Requesting: {url}")
        async with aiohttp.request("GET", url) as response:
            try:
                match response.status:
                    case 200:
                        return await response.json()
                    case 429:
                        raise Exception("Rate limit exceeded")
                    case _:
                        raise Exception(f"Error: {response.status}")
            except aiohttp.ContentTypeError:
                raise Exception("Invalid response format")