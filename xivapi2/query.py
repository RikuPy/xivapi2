import urllib.parse
from typing import Literal, Self

Operator = Literal["=", "~", ">", "<", ">=", "<="]
Language = Literal["ja", "en", "de", "fr", "chs", "cht", "kr"]


class QueryBuilder:
    def __init__(self, *sheets: str):
        self._fields: list[str] = []
        self._transients: list[str] = []
        self._sheets: list[str] = list(sheets)
        self._filters: list[tuple[str, Operator, str]] = []
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

    def filter(self, field: str, operator: Operator, value: str | int | float) -> Self:
        self._filters.append((field, operator, value))
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
            _filters = " ".join(
                f'{field}{operator}"{value.replace('"', "%22")}"'
                for field, operator, value in self._filters
            )
            query_params["query"] = f"({_filters})"
        if self._limit:
            query_params["limit"] = self._limit
        if self._version:
            query_params["version"] = self._version
        if self._lang:
            query_params["language"] = self._lang
        if self._schema:
            query_params["schema"] = self._schema

        return urllib.parse.urlencode(query_params)


q = (
    QueryBuilder("Item")
    .add_fields("Name", "Description")
    .filter("Name", "~", "steak")
    .filter("Description", "~", "dzo")
    .set_version(7.2)
    .limit(10)
)
