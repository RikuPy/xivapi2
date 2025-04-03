import asyncio

from xivapi2 import QueryBuilder, FilterGroup, XivApiClient

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

c = XivApiClient()
r = asyncio.run(c.search(q))
rs = [_rs for _rs in r]
print(r)