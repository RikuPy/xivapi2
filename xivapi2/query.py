import urllib.parse
from dataclasses import dataclass
from typing import Literal, Self, overload

__all__ = ["QueryBuilder", "FilterGroup"]

type Operator = Literal["=", "~", ">", "<", ">=", "<="]
type Language = Literal["ja", "en", "de", "fr", "chs", "cht", "kr"]
type Value = str | int | float | bool


@dataclass(slots=True)
class Filter:
    field: str
    operator: Operator
    value: Value

    def build(self):
        param = f'{self.field}{self.operator}'
        if isinstance(self.value, str):
            param += f'"{self.value.replace('"', "%22")}"'
        else:
            param += str(self.value).lower()

        return param


class FilterGroup:
    def __init__(self):
        self._filters: list[tuple[Filter, bool]] = []

    def filter(
        self, field: str, operator: Operator, value: Value, *, exclude: bool = False
    ) -> Self:
        self._filters.append((Filter(field, operator, value), exclude))
        return self

    def build(self):
        filters_ = " ".join(f"{'-' if exclude else '+'}{filter_.build()}" for filter_, exclude in self._filters)
        return f"({filters_})"


class QueryBuilder:
    def __init__(self, *sheets: str):
        self._fields: list[str] = []
        self._transients: list[str] = []
        self._sheets: list[str] = list(sheets)
        self._filters: list[tuple[Filter | FilterGroup, bool]] = []
        self._limit: int | None = None
        self._version: str | None = None
        self._lang: str | None = None
        self._schema: str | None = None

    def add_fields(self, *fields: str) -> Self:
        self._fields.extend(fields)
        return self

    def add_transients(self, *transients: str) -> Self:
        self._transients.extend(transients)
        return self

    def add_sheets(self, *sheets: str) -> Self:
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
            raise TypeError("field_or_group must be a string containing a field name or a FilterGroup instance")

        return self

    def limit(self, limit: int) -> Self:
        self._limit = limit
        return self

    def set_version(self, version: float | str | None) -> Self:
        self._version = version
        return self

    def set_language(self, lang: Language) -> Self:
        self._lang = lang
        return self

    def set_schema(self, schema: str) -> Self:
        self._schema = schema
        return self

    def build(self):
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
            query_params["limit"] = self._limit
        if self._version:
            query_params["version"] = self._version
        if self._lang:
            query_params["language"] = self._lang
        if self._schema:
            query_params["schema"] = self._schema

        return urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)


q = (
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
