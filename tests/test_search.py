import pytest

from xivapi2 import FilterGroup, QueryBuilder, XivApiClient


@pytest.mark.asyncio
async def test_search():
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

    client = XivApiClient()
    results = await client.search(query)
    assert results
    assert results[0]["score"] > 1.0
    for result in results:
        assert result["fields"]["Name"]
        assert result["fields"]["Description"]
        assert "steak" in result["fields"]["Name"].lower()
        assert "eft" not in result["fields"]["Name"].lower()
