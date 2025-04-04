async def test_version_names(client):
    versions = await client.versions()
    assert versions
    for version in versions:
        assert version.names
        assert isinstance(version.names, list)
        assert str(version) == version.names[0]
