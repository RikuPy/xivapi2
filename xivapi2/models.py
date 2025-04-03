from dataclasses import dataclass


@dataclass(kw_only=True)
class SearchResults:
    results: list[dict]
    schema: str

    def __getitem__(self, item):
        return self.results[item]

    def __iter__(self):
        return iter(self.results)

    def __bool__(self):
        return bool(self.results)
