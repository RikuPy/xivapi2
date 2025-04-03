import logging
import urllib.parse
from typing import Literal, overload

import aiohttp

from xivapi2.models import RowResult, SearchResponse, SearchResult, SheetResponse, Version
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
        response = await self._request(
            f"{self.base_url}/sheet/{sheet}?{urllib.parse.urlencode(query_params)}"
        )
        return SheetResponse(
            schema=response["schema"],
            rows=[
                RowResult(
                    row_id=row["row_id"],
                    subrow_id=row.get("subrow_id"),
                    fields=row["fields"],
                    transient=row.get("transient"),
                )
                for row in response["rows"]
            ],
        )

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
        response = await self._request(
            f"{self.base_url}/sheet/{sheet}/{row}?{urllib.parse.urlencode(query_params)}"
        )
        return RowResult(
            row_id=response["row_id"],
            subrow_id=response.get("subrow_id"),
            fields=response["fields"],
            transient=response.get("transient"),
        )

    async def search(self, query: QueryBuilder) -> SearchResponse:
        response = await self._request(f"{self.base_url}/search?{query.build()}")
        return SearchResponse(
            schema=response["schema"],
            results=[
                SearchResult(
                    score=result["score"],
                    sheet=result["sheet"],
                    row_id=result["row_id"],
                    subrow_id=result.get("subrow_id"),
                    fields=result["fields"],
                    transient=result.get("transient"),
                )
                for result in response["results"]
            ],
        )

    async def get_asset(
        self, path: str, format_: Literal["jpg", "png", "webp"], *, version: str = None
    ) -> bytes:
        query_params = {"path": path, "format": format_}
        if version:
            query_params["version"] = version
        return await self._request(
            f"{self.base_url}/asset?{urllib.parse.urlencode(query_params)}", asset=True
        )

    async def get_map(self, territory: str, index: str, *, version: str | None = None) -> bytes:
        query_params = {}
        if version:
            query_params["version"] = version
        return await self._request(
            f"{self.base_url}/asset/map/{territory}/{index}?{urllib.parse.urlencode(query_params)}",
            asset=True,
        )

    async def versions(self):
        response = await self._request(f"{self.base_url}/version")
        return [Version(v["names"]) for v in response["versions"]]

    @overload
    async def _request(self, url: str, asset: Literal[False] = False) -> dict: ...

    @overload
    async def _request(self, url: str, asset: Literal[True]) -> bytes: ...

    async def _request(self, url: str, asset: bool = False) -> dict | bytes:
        self._logger.debug(f"Requesting: {url}")
        async with aiohttp.request("GET", url) as response:
            try:
                match response.status:
                    case 200:
                        if asset:
                            return await response.read()
                        else:
                            return await response.json()
                    case 429:
                        raise Exception("Rate limit exceeded")
                    case _:
                        raise Exception(f"Error: {response.status}")
            except aiohttp.ContentTypeError:
                raise Exception("Invalid response format")
