from xivapi2 import FilterGroup, QueryBuilder, XivApiClient


async def test_search(client: XivApiClient):
    # fmt: off
    query = (
        QueryBuilder("Item")
        .add_fields("Name", "Description")
        .filter("IsUntradable", "=", False)
        .filter(
            FilterGroup()
            .filter("Name", "~", "Gemdraught")
            .filter("Name", "~", "Vitality", exclude=True)
        )
        .set_version(7.2)
    )
    # fmt: on

    results = [r async for r in client.search(query)]
    assert results[0].score > 1.0
    for result in results:
        assert result.fields["Name"]
        assert result.fields["Description"]
        assert "gemdraught" in result.fields["Name"].lower()
        assert "vitality" not in result.fields["Name"].lower()
        assert result.schema


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
