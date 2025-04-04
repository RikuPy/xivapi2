import logging
import urllib.parse
from typing import AsyncGenerator, Literal, overload

import aiohttp

from xivapi2.errors import (
    XivApiError,
    XivApiNotFoundError,
    XivApiParameterError,
    XivApiRateLimitError,
    XivApiServerError,
)
from xivapi2.models import RowResult, SearchResult, Version
from xivapi2.query import Language, QueryBuilder
from xivapi2.utils import Throttler

__all__ = ["XivApiClient"]


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
        self.base_url = "https://v2.xivapi.com/api/"
        self._logger = logging.getLogger()
        self._throttler = Throttler(5, 1.0)
        self._session: aiohttp.ClientSession | None = None

    async def sheets(self) -> list[str]:
        """
        Retrieves a list of all available sheets.

        To query for rows in a specific sheet, use the :meth:`sheet_rows` method. To get detailed information about
        a specific row, use the :meth:`get_sheet_row` method.

        Returns:
            list[str]: A list of sheet names.

        Raises:
            XivApiServerError: xivapi returned an internal server error.
        """
        async with aiohttp.ClientSession(self.base_url) as session:
            response = await self._request(session, "sheet")
        return [s["name"] for s in response["sheets"]]

    async def sheet_rows(
        self,
        sheet: str,
        *,
        rows: list[int] | None = None,
        fields: list[str] | None = None,
        after: int | None = None,
        limit: int | None = None,
        transients: list[str] | None = None,
        language: Language | None = None,
        schema: str | None = None,
    ) -> AsyncGenerator[RowResult, None]:
        """
        Retrieves rows from a specific sheet.

        To retrieve a list of available sheets, use the :meth:`sheets` method.

        Args:
            sheet (str): The name of the sheet to query. This is case-sensitive.
            rows (list[int] | None): A list of row IDs to retrieve. If not provided, all rows will be queried.
            fields (list[str] | None): A list of field names to retrieve. If not provided, all fields will be retrieved.
            after (int | None): The row ID to start retrieving from.
            limit (int | None): Maximum number of rows to return.
            transients (list[str] | None): Data fields to read for selected rows' transient row, if any is present.
            language (Language | None): The default language to use for the results.
            schema (str | None): The schema that row data should be read with.

        Returns:
            SheetResponse: An iterable containing a list of :meth:`RowResult`'s.

        Raises:
            XivApiNotFoundError: The requested sheet could not be found.
            XivApiParameterError: One or more of the passed parameters were invalid.
            XivApiServerError: xivapi returned an internal server error.
        """
        query_params = {
            key: value
            for key, value in [
                ("rows", ",".join(map(str, rows)) if rows else None),
                ("fields", ",".join(fields) if fields else None),
                ("after", after),
                ("limit", limit or 500),
                ("transient", ",".join(transients) if transients else None),
                ("language", language),
                ("schema", schema),
            ]
            if value is not None
        }
        async with aiohttp.ClientSession(self.base_url) as session:
            response = await self._request(
                session, f"sheet/{sheet}?{urllib.parse.urlencode(query_params)}"
            )

            index = 0
            while response["rows"]:
                for row in response["rows"]:
                    yield RowResult(
                        row_id=row["row_id"],
                        subrow_id=row.get("subrow_id"),
                        fields=row["fields"],
                        transients=row.get("transient", {}),
                    )

                    index += 1
                    if limit and index >= limit:
                        return

                # If we've requested explicit rows, skip any pagination and return immediately
                if rows:
                    return

                query_params["after"] = response["rows"][-1]["row_id"]
                if limit:
                    query_params["limit"] = limit - index
                response = await self._request(
                    session, f"sheet/{sheet}?{urllib.parse.urlencode(query_params)}"
                )

    async def get_sheet_row(
        self,
        sheet: str,
        row: int,
        *,
        fields: list[str] | None = None,
        transients: list[str] | None = None,
        language: Language | None = None,
        schema: str | None = None,
    ) -> RowResult:
        """
        Retrieves a specific row from a sheet.

        Args:
            sheet (str): The name of the sheet to query. This is case-sensitive.
            row (int): The ID of the row to retrieve.
            fields (list[str] | None): A list of field names to retrieve. If not provided, all fields will be retrieved.
            transients (list[str] | None): Data fields to read for selected rows' transient row, if any is present.
            language (Language | None): The default language to use for the results.
            schema (str | None): The schema that row data should be read with.

        Returns:
            RowResult: A dataclass containing the rows fields and transient data, if any is present.

        Raises:
            XivApiNotFoundError: The requested sheet or row could not be found.
            XivApiParameterError: One or more of the passed parameters were invalid.
            XivApiServerError: xivapi returned an internal server error.
        """
        query_params = {
            key: value
            for key, value in [
                ("fields", ",".join(fields) if fields else None),
                ("transient", ",".join(transients) if transients else None),
                ("language", language),
                ("schema", schema),
            ]
            if value is not None
        }
        async with aiohttp.ClientSession(self.base_url) as session:
            response = await self._request(
                session, f"sheet/{sheet}/{row}?{urllib.parse.urlencode(query_params)}"
            )
            return RowResult(
                row_id=response["row_id"],
                subrow_id=response.get("subrow_id"),
                fields=response["fields"],
                transients=response.get("transient", {}),
            )

    async def search(self, query: QueryBuilder) -> AsyncGenerator[SearchResult, None]:
        """
        Searches for matching rows in a specific sheet using a query builder.

        Example:
            .. code:: python

                import asyncio
                from xivapi2 import XivApiClient
                from xivapi2.query import QueryBuilder, FilterGroup

                async def main():
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
                    async for result in client.search(query):
                        print(f"[{result.row_id}] {result.fields['Name']}")
                        print(result.fields["Description"])
                        print("-" * 32)
                asyncio.run(main())

        Args:
            query (QueryBuilder): The query builder object containing the search parameters.

        Returns:
            SearchResponse: An iterable containing the search results.

        Raises:
            XivApiParameterError: One or more of the passed search parameters were invalid.
            XivApiServerError: xivapi returned an internal server error.
        """
        async with aiohttp.ClientSession(self.base_url) as session:
            response = await self._request(session, f"search?{query.build()}")

            index = 0
            while True:
                for result in response["results"]:
                    yield SearchResult(
                        score=result["score"],
                        sheet=result["sheet"],
                        row_id=result["row_id"],
                        subrow_id=result.get("subrow_id"),
                        fields=result["fields"],
                        transients=result.get("transient"),
                    )

                    index += 1
                    if query.get_limit() and index >= query.get_limit():
                        return

                cursor = response.get("next")
                if cursor:
                    response = await self._request(session, f"search?{query.build(cursor=cursor)}")
                else:
                    return

    async def get_asset(
        self, path: str, format_: Literal["jpg", "png", "webp"], *, version: str | None = None
    ) -> bytes:
        """
        Retrieves an asset from the XivAPI as bytes.

        Args:
            path (str): The path to the asset. Paths to icons and other assets can be found in their relevant sheets.
            format_ (str): The format of the asset. Can be "jpg", "png", or "webp".
            version (str | None): The version of the asset to retrieve. Defaults to the latest version.

        Returns:
            bytes: The image as bytes.

        Raises:
            XivApiNotFoundError: The requested asset could not be found.
            XivApiParameterError: An invalid image format was specified.
            XivApiServerError: xivapi returned an internal server error.
        """
        query_params = {"path": path, "format": format_}
        if version:
            query_params["version"] = version
        async with aiohttp.ClientSession(self.base_url) as session:
            return await self._request(
                session, f"asset?{urllib.parse.urlencode(query_params)}", asset=True
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

        Raises:
            XivApiNotFoundError: The requested map asset could not be found.
            XivApiParameterError: An invalid map territory or index was specified.
            XivApiServerError: xivapi returned an internal server error.
        """
        query_params = {}
        if version:
            query_params["version"] = version
        async with aiohttp.ClientSession(self.base_url) as session:
            return await self._request(
                session,
                f"asset/map/{territory}/{index}?{urllib.parse.urlencode(query_params)}",
                asset=True,
            )

    async def versions(self):
        """
        Returns metadata about the versions recorded by the boilmaster system

        Returns:
            list[Version]: A list of versions understood by the API.

        Raises:
            XivApiServerError: xivapi returned an internal server error.
        """
        async with aiohttp.ClientSession(self.base_url) as session:
            response = await self._request(session, "version")
        return [Version(v["names"]) for v in response["versions"]]

    @overload
    async def _request(
        self, session: aiohttp.ClientSession, url: str, asset: Literal[False] = False
    ) -> dict: ...

    @overload
    async def _request(
        self, session: aiohttp.ClientSession, url: str, asset: Literal[True]
    ) -> bytes: ...

    async def _request(
        self, session: aiohttp.ClientSession, url: str, asset: bool = False
    ) -> dict | bytes:
        self._logger.debug(f"Requesting: {url}")
        async with self._throttler:
            async with session.request("GET", url) as response:
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
                            raise XivApiError(
                                f"An unknown {response.status} error code was returned from XivApi"
                            )
                except aiohttp.ContentTypeError:
                    raise XivApiError(
                        "An unknown error occurred while processing the response from XivApi"
                    )
