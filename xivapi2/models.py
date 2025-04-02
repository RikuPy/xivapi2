from dataclasses import dataclass


@dataclass
class SearchResults:
    schema: str
    results: list[dict]

    def __getitem__(self, item):
        return self.results[item]

    def __iter__(self):
        return iter(self.results)

    def __bool__(self):
        return bool(self.results)