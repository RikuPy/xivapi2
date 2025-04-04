from xivapi2 import FilterGroup, QueryBuilder, XivApiClient


async def test_search(client: XivApiClient):
    # fmt: off
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
    # fmt: on

    results = [r async for r in client.search(query)]
    assert results[0].score > 1.0
    for result in results:
        assert result.fields["Name"]
        assert result.fields["Description"]
        assert "steak" in result.fields["Name"].lower()
        assert "eft" not in result.fields["Name"].lower()


async def test_paginated_search(client: XivApiClient):
    # fmt: off
    query = (
        QueryBuilder("Item")
        .add_fields("Name")
        .filter("IsUntradable", "=", False)
        .set_version(7.2)
        .limit(525)
    )
    # fmt: on

    results = [r async for r in client.search(query)]
    assert len(results) == 525
