from dataclasses import dataclass, field

__all__ = ["SearchResult", "RowResult", "Version"]


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
        schema (str): The canonical specifier for the schema used in this response.
    """

    score: float
    sheet: str
    row_id: int
    subrow_id: int | None = None
    fields: dict
    transients: dict = field(default_factory=dict)
    schema: str


@dataclass(kw_only=True, slots=True)
class RowResult:
    """
    Represents a single row result.

    Attributes:
        row_id (int): The ID of the row.
        subrow_id (int | None): The subrow ID, when relevant.
        fields (dict): The fields of the row result.
        transients (dict): Transient data, when relevant.
        schema (str): The canonical specifier for the schema used in this response.
    """

    row_id: int
    subrow_id: int | None = None
    fields: dict
    transients: dict = field(default_factory=dict)
    schema: str


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
