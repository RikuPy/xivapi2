import logging
import urllib.parse
from typing import Literal, overload, Any, AsyncGenerator

import aiohttp

from xivapi2.errors import (
    XivApiParameterError,
    XivApiRateLimitError,
    XivApiNotFoundError,
    XivApiServerError,
    XivApiError,
)
from xivapi2.models import RowResult, SearchResponse, SearchResult, SheetResponse, Version
from xivapi2.query import Language, QueryBuilder


class XivApiClient:
    """
    An asynchronous client for `XivAPIv2 <https://v2.xivapi.com/>`__.

    Example:
        .. code:: python

            import asyncio
            from xivapi2 import XivApiClient

            client = XivApiClient()
            sheet = asyncio.run(client.get_sheet_row("Item", 12056, fields=["Name", "Description"]))
            print(sheet.fields["Name"])  # Lesser Panda
            print(sheet.fields["Description"])
    """
    def __init__(self):
        self.base_url = "https://v2.xivapi.com/api"
        self._logger = logging.getLogger()

    async def sheets(self) -> list[str]:
        """
        Retrieves a list of all available sheets.

        To query for rows in a specific sheet, use the :meth:`sheet_rows` method. To get detailed information about
        a specific row, use the :meth:`get_sheet_row` method.

        Returns:
            list[str]: A list of sheet names.
        """
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
    ) -> AsyncGenerator[RowResult]:
        """
        Retrieves rows from a specific sheet.

        To retrieve a list of available sheets, use the :meth:`sheets` method.

        Args:
            sheet (str): The name of the sheet to query. This is case-sensitive.
            rows (list[int] | None): A list of row IDs to retrieve. If not provided, all rows will be queried.
            fields (list[str] | None): A list of field names to retrieve. If not provided, all fields will be retrieved.
            after (int | None): The row ID to start retrieving from.
            limit (int | None): Maximum number of rows to return (up to 500). Defaults to 500.
            transient (str | None): Data fields to read for selected rows' transient row, if any is present.
            language (Language | None): The default language to use for the results.
            schema (str | None): The schema that row data should be read with.

        Returns:
            SheetResponse: An iterable containing a list of :meth:`RowResult`'s.
        """
        query_params = {
            key: value
            for key, value in [
                ("rows", ",".join(map(str, rows)) if rows else None),
                ("fields", ",".join(fields) if fields else None),
                ("after", after),
                ("limit", limit or 500),
                ("transient", transient),
                ("language", language),
                ("schema", schema),
            ]
            if value is not None
        }
        response = await self._request(
            f"{self.base_url}/sheet/{sheet}?{urllib.parse.urlencode(query_params)}"
        )

        index = 0
        while response["rows"]:
            for row in response["rows"]:
                yield RowResult(
                    row_id=row["row_id"],
                    subrow_id=row.get("subrow_id"),
                    fields=row["fields"],
                    transient=row.get("transient"),
                )

                index += 1
                if limit and index >= limit:
                    break

            query_params["after"] = response["rows"][-1]["row_id"]
            if limit:
                query_params["limit"] = limit - index
            response = await self._request(
                f"{self.base_url}/sheet/{sheet}?{urllib.parse.urlencode(query_params)}"
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
    ) -> RowResult:
        """
        Retrieves a specific row from a sheet.

        Args:
            sheet (str): The name of the sheet to query. This is case-sensitive.
            row (int): The ID of the row to retrieve.
            fields (list[str] | None): A list of field names to retrieve. If not provided, all fields will be retrieved.
            transient (str | None): Data fields to read for selected rows' transient row, if any is present.
            language (Language | None): The default language to use for the results.
            schema (str | None): The schema that row data should be read with.

        Returns:
            RowResult: A dataclass containing the rows fields and transient data, if any is present.
        """
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
        """
        Searches for matching rows in a specific sheet using a query builder.

        Example:
            .. code:: python

                import asyncio
                from xivapi2 import XivApiClient
                from xivapi2.query import QueryBuilder, FilterGroup

                client = XivApiClient()
                query = (
                    QueryBuilder("Item")
                    .add_fields("Name", "Description")
                    .filter("IsUntradable", "=", False)
                    .filter(
                        FilterGroup()
                        .filter("Name", "~", "Steak")
                        .filter("Name", "~", "eft", exclude=True)
                    )
                    .set_version(7.2)
                    .limit(10)
                )
                search_results = asyncio.run(client.search(query))
                for result in search_results:
                    print(f"[{result.row_id}] {result.fields['Name']}")
                    print(result.fields["Description"])
                    print("-" * 32)

        Args:
            query (QueryBuilder): The query builder object containing the search parameters.

        Returns:
            SearchResponse: An iterable containing the search results.
        """
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
        """
        Retrieves an asset from the XivAPI as bytes.

        Args:
            path (str): The path to the asset. Paths to icons and other assets can be found in their relevant sheets.
            format_ (str): The format of the asset. Can be "jpg", "png", or "webp".
            version (str | None): The version of the asset to retrieve. Defaults to the latest version.

        Returns:
            bytes: The image as bytes.
        """
        query_params = {"path": path, "format": format_}
        if version:
            query_params["version"] = version
        return await self._request(
            f"{self.base_url}/asset?{urllib.parse.urlencode(query_params)}", asset=True
        )

    async def get_map(self, territory: str, index: str, *, version: str | None = None) -> bytes:
        """
        Composes and returns a map asset image as bytes.

        Args:
            territory (str): Territory of the map to be retrieved. This typically takes the form of 4 characters,
                [letter][number][letter][number].
            index (str): Index of the map within the territory. This invariably takes the form of a two-digit
                zero-padded number..
            version (str | None): The version of the asset to retrieve. Defaults to the latest version.

        Returns:
            bytes: The map asset as bytes.
        """
        query_params = {}
        if version:
            query_params["version"] = version
        return await self._request(
            f"{self.base_url}/asset/map/{territory}/{index}?{urllib.parse.urlencode(query_params)}",
            asset=True,
        )

    async def versions(self):
        """
        Returns metadata about the versions recorded by the boilmaster system

        Returns:
            list[Version]: A list of versions understood by the API.
        """
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
                    case 400:
                        raise XivApiParameterError((await response.json()).get("message"))
                    case 404:
                        raise XivApiNotFoundError((await response.json()).get("message"))
                    case 429:
                        raise XivApiRateLimitError((await response.json()).get("message"))
                    case 500:
                        raise XivApiServerError((await response.json()).get("message"))
                    case _:
                        raise XivApiError(f"An unknown {response.status} error code was returned from XivApi")
            except aiohttp.ContentTypeError:
                raise XivApiError("An unknown error occurred while processing the response from XivApi")
