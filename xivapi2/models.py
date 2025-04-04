from dataclasses import dataclass, field

__all__ = ["SearchResult", "SearchResponse", "RowResult", "SheetResponse", "Version"]


@dataclass(kw_only=True, slots=True)
class SearchResult:
    """
    Represents a single search result.

    Attributes:
        score (float): Relevance score for this entry. These values only loosely represent the relevance of an entry
            to the search query. No guarantee is given that the discrete values, nor resulting sort order,
            will remain stable
        sheet (str): The name of the sheet this result was found in.
        row_id (int): The ID of the row.
        subrow_id (int | None): The subrow ID, when relevant.
        fields (dict): The fields of the search result.
        transients (dict): Transient data, when relevant.
    """

    score: float
    sheet: str
    row_id: int
    subrow_id: int | None = None
    fields: dict
    transients: dict = field(default_factory=dict)


@dataclass(kw_only=True)
class SearchResponse:
    """
    Represents a search response. This can be iterated or indexed like a list.

    Attributes:
        schema (str): The schema of the search response.
        results (list[SearchResult]): A list of search results.
    """

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
    """
    Represents a single row result.

    Attributes:
        row_id (int): The ID of the row.
        subrow_id (int | None): The subrow ID, when relevant.
        fields (dict): The fields of the row result.
        transients (dict): Transient data, when relevant.
    """

    row_id: int
    subrow_id: int | None = None
    fields: dict
    transients: dict = field(default_factory=dict)


@dataclass(kw_only=True)
class SheetResponse:
    """
    Represents a sheet response. This can be iterated or indexed like a list.

    Attributes:
        schema (str): The schema of the sheet response.
        rows (list[RowResult]): A list of row results.
    """

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
    Represents a game version understood by the API.
    """

    names: list[str]

    def __str__(self):
        """
        Currently, the versions endpoint always returns lists of one version element, and casting this dataclass to a
        string will return that first element by default.
        """
        return self.names[0]
