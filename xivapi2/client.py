import logging
import urllib.parse

import aiohttp

from xivapi2.models import SearchResults
from xivapi2.query import Language, QueryBuilder


class XivApiClient:
    def __init__(self):
        self.base_url = "https://v2.xivapi.com/api"
        self._logger = logging.getLogger()

    async def sheets(self):
        resp = await self._request(f"{self.base_url}/sheet")
        return [s["name"] for s in resp["sheets"]]

    async def sheet_rows(
        self,
        sheet: str,
        *,
        rows: list[int] | None = None,
        fields: list[str] | None = None,
        after: int | None = None,
        limit: int | None = None,
        transient: str | None = None,
        language: Language | None = None,
        schema: str | None = None,
    ):
        query_params = {
            key: value
            for key, value in [
                ("rows", ",".join(map(str, rows)) if rows else None),
                ("fields", ",".join(fields) if fields else None),
                ("after", after),
                ("limit", limit),
                ("transient", transient),
                ("language", language),
                ("schema", schema),
            ]
            if value is not None
        }

        resp = await self._request(
            f"{self.base_url}/sheet/{sheet}?{urllib.parse.urlencode(query_params)}"
        )
        return resp["rows"]

    async def get_sheet_row(
        self,
        sheet: str,
        row: int,
        *,
        fields: list[str] | None = None,
        transient: str | None = None,
        language: Language | None = None,
        schema: str | None = None,
    ):
        query_params = {
            key: value
            for key, value in [
                ("fields", ",".join(fields) if fields else None),
                ("transient", transient),
                ("language", language),
                ("schema", schema),
            ]
            if value is not None
        }

        resp = await self._request(
            f"{self.base_url}/sheet/{sheet}/{row}?{urllib.parse.urlencode(query_params)}"
        )
        return resp["fields"]

    async def search(self, query: QueryBuilder) -> SearchResults:
        resp = await self._request(f"{self.base_url}/search?{query.build()}")
        return SearchResults(results=resp["results"], schema=resp["schema"])

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
