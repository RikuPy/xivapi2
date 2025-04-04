import urllib.parse
from dataclasses import dataclass
from typing import Literal, Self, overload

__all__ = ["QueryBuilder", "FilterGroup"]

type Operator = Literal["=", "~", ">", "<", ">=", "<="]
type Language = Literal["ja", "en", "de", "fr", "chs", "cht", "kr"]
type Value = str | int | float | bool


@dataclass(slots=True)
class Filter:
    """
    .. warning:: This class is intended for internal use only.

    A dataclass for internal use that represents a filter for the search query.

    Attributes:
        field (str): The field to filter on.
        operator (Operator): The operator to use for the filter.
        value (Value): The value to filter by.
    """

    field: str
    operator: Operator
    value: Value

    def build(self) -> str:
        """
        Builds the filter string for the query.

        Returns:
            str: The compiled filter string.
        """
        param = f"{self.field}{self.operator}"
        if isinstance(self.value, str):
            param += f'"{self.value.replace('"', "%22")}"'
        else:
            param += str(self.value).lower()

        return param


class FilterGroup:
    """
    A class used to build grouped filter clauses for a search query.

    For more information on how grouped clauses work, refer to the XivAPI documentation:
    https://v2.xivapi.com/docs/guides/search/#filtering-results
    """

    def __init__(self):
        self._filters: list[tuple[Filter, bool]] = []

    def filter(
        self, field: str, operator: Operator, value: Value, *, exclude: bool = False
    ) -> Self:
        """
        Adds a filter to the group.

        Args:
            field (str): The field to filter on.
            operator (Operator): The operator to use for the filter.
            value (Value): The value to filter by.
            exclude (bool): Whether to exclude this filter clause from the search results. Defaults to False.

        Returns:
            Self: The current instance of FilterGroup for method chaining.
        """
        self._filters.append((Filter(field, operator, value), exclude))
        return self

    def build(self):
        """
        .. warning:: This function is intended for internal use only.

        builds the filter group into a query string.

        Returns:
            str: The compiled filter group string.
        """
        filters_ = " ".join(
            f"{'-' if exclude else '+'}{filter_.build()}" for filter_, exclude in self._filters
        )
        return f"({filters_})"


class QueryBuilder:
    """
    A class used to build search queries for use in the :meth:`XivApiClient.search` method.

    Example:
        .. code:: python

            query = (
                QueryBuilder("Item")  # Query the "Item" sheet
                .add_fields("Name", "Description")  # Include the Name and Description fields in the results
                .filter("IsUntradable", "=", False)  # Can be traded
                .filter(
                    FilterGroup()
                    .filter("Name", "~", "Steak")  # Contains "Steak"
                    .filter("Name", "~", "eft", exclude=True)  # But does not contain "eft"
                )
                .set_version(7.2)
                .limit(10)
            )
    """

    def __init__(self, *sheets: str):
        self._fields: list[str] = []
        self._transients: list[str] = []
        self._sheets: list[str] = list(sheets)
        self._filters: list[tuple[Filter | FilterGroup, bool]] = []
        self._limit: int | None = None
        self._version: str | float | None = None
        self._lang: str | None = None
        self._schema: str | None = None

    def add_fields(self, *fields: str) -> Self:
        """
        Adds fields to the query.

        Args:
            *fields (str): The fields to include in the search results.

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        self._fields.extend(fields)
        return self

    def add_transients(self, *transients: str) -> Self:
        """
        Data fields to read for selected rows' transient row, if any are present.

        Args:
            *transients: The transient fields to include in the search results.

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        self._transients.extend(transients)
        return self

    def add_sheets(self, *sheets: str) -> Self:
        """
        Adds sheets to the query.

        Args:
            *sheets: The sheets to search against.

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        self._sheets.extend(sheets)
        return self

    @overload
    def filter(
        self,
        field: str,
        operator: Operator,
        value: Value,
        *,
        exclude: bool = False,
    ) -> Self: ...

    @overload
    def filter(self, filter_group: FilterGroup, *, exclude: bool = False) -> Self: ...

    def filter(
        self,
        field_or_group: str | FilterGroup,
        operator: Operator | None = None,
        value: Value | None = None,
        *,
        exclude: bool = False,
    ) -> Self:
        """
        Adds a filter to the query. This can be a single filter or a filter group.

        See :class:`FilterGroup` for more information on how to build grouped filter clauses.

        Args:
            field_or_group (str | FilterGroup): The field name or a FilterGroup instance.
            operator (Operator | None): The operator to use for the filter. Required if field_or_group is a string.
            value (Value | None): The value to filter by. Required if field_or_group is a string.
            exclude (bool): Whether to exclude this filter clause from the search results. Defaults to False.

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        # Standard filter
        if isinstance(field_or_group, str):
            if operator is None:
                raise ValueError("Operator cannot be None when a field name is provided")
            if value is None:
                raise ValueError("Value cannot be None when a field name is provided")

            self._filters.append((Filter(field_or_group, operator, value), exclude))
        # Grouped filter
        elif isinstance(field_or_group, FilterGroup):
            self._filters.append((field_or_group, exclude))
        else:
            raise TypeError(
                "field_or_group must be a string containing a field name or a FilterGroup instance"
            )

        return self

    def limit(self, limit: int) -> Self:
        """
        Sets the maximum number of results to return.

        Args:
            limit (int): The maximum number of results to return.

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        self._limit = limit
        return self

    def set_version(self, version: float | str | None) -> Self:
        """
        Sets the game version to use for the query.

        Args:
            version: The version of the API to use for the query.

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        self._version = version
        return self

    def set_language(self, lang: Language) -> Self:
        """
        Sets the default language for the query.

        Args:
             lang(Language): The language to use for the query. This can be one of the following:
                - "ja" (Japanese)
                - "en" (English)
                - "de" (German)
                - "fr" (French)
                - "chs" (Simplified Chinese)
                - "cht" (Traditional Chinese)
                - "kr" (Korean)

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        self._lang = lang
        return self

    def set_schema(self, schema: str) -> Self:
        """
        Sets the schema for the query.

        Args:
            schema: The schema to use for the query.

        Returns:
            Self: The current instance of QueryBuilder for method chaining.
        """
        self._schema = schema
        return self

    def get_limit(self) -> int | None:
        """
        Returns the current limit set for the query.

        Returns:
            int | None: The current limit or None if not set.
        """
        return self._limit

    def build(self, cursor: str | None = None) -> str:
        """
        .. warning:: This function is intended for internal use only.

        Builds the query string for the search.

        Args:
            cursor (str | None): The cursor for pagination.

        Returns:
            str: The compiled query string.
        """
        query_params = {"sheets": ",".join(self._sheets)}
        if self._fields:
            query_params["fields"] = ",".join(self._fields)
        if self._transients:
            query_params["transient"] = ",".join(self._transients)
        if self._filters:
            query_params["query"] = " ".join(
                f"{'-' if exclude else '+'}{filter_.build()}" for filter_, exclude in self._filters
            )
        if self._limit:
            query_params["limit"] = str(self._limit)
        if self._version:
            query_params["version"] = str(self._version)
        if self._lang:
            query_params["language"] = self._lang
        if self._schema:
            query_params["schema"] = self._schema
        if cursor:
            query_params["cursor"] = cursor

        return urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
