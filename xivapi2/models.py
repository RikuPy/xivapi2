from dataclasses import dataclass


@dataclass(kw_only=True, slots=True)
class SearchResult:
    score: float
    sheet: str
    row_id: int
    subrow_id: int | None = None
    fields: dict
    transient: dict | None = None


@dataclass(kw_only=True)
class SearchResponse:
    schema: str
    results: list[SearchResult]

    def __bool__(self):
        return bool(self.results)

    def __getitem__(self, item):
        return self.results[item]

    def __iter__(self):
        return iter(self.results)

    def __len__(self):
        return len(self.results)


@dataclass(kw_only=True, slots=True)
class RowResult:
    row_id: int
    subrow_id: int | None = None
    fields: dict
    transient: dict | None = None


@dataclass(kw_only=True)
class SheetResponse:
    schema: str
    rows: list[RowResult]

    def __bool__(self):
        return bool(self.rows)

    def __getitem__(self, item):
        return self.rows[item]

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)


@dataclass(slots=True)
class Version:
    """
    Represents a version of a sheet.
    """
    names: list[str]

    def __str__(self):
        """
        This is kind of a hacky simplification. Currently, the versions endpoint always returns lists of one
        version element, but it's possible this may change in the future. So, I've created a dataclass to hold
        the entire list of names in-case that does happen, but still allow str() casting for ease of reference.
        """
        return self.names[0]
