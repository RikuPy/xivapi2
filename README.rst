Overview
========

xivapi2 is an unofficial asynchronous Python library for `xivapi <https://v2.xivapi.com/>`__.

Installation
============

You can install this library using pip:

.. code:: shell

   pip install xivapi2

Usage
=====

Interacting with sheets
-----------------------

To get a list of sheets currently supported by xivapi, you can use the
``sheets`` method:

.. code:: python

    import asyncio
    from xivapi2 import XivApiClient

    async def main():
        client = XivApiClient()
        sheets = await client.sheets()
        for sheet in sheets:
            print(sheet)

    asyncio.run(main())


To list what rows a specific sheet has, you can use the
``sheet_rows`` method:

.. code:: python

    import asyncio
    from xivapi2 import XivApiClient

    async def main():
        client = XivApiClient()
        async for row in client.sheet_rows("Item", fields=["Name", "Description"], limit=40):
            print(f"ID: {row.row_id}, Name: {row.fields["Name"]}, Description: {row.fields["Description"]}")

    asyncio.run(main())

To get detailed information on a specific row, you can use the
``get_sheet_row`` method:

.. code:: python

    import asyncio
    from xivapi2 import XivApiClient

    async def main():
        client = XivApiClient()
        row = await client.get_sheet_row("Item", 12056)
        print(row.fields["Name"])
        print(row.fields["Description"])

    row = asyncio.run(main())


Searching
---------
To search for data in a specific sheet, you can use the ``search`` method.

First, construct a search query using the ``QueryBuilder`` class.

.. code:: python

    import asyncio
    from xivapi2 import XivApiClient, QueryBuilder, FilterGroup

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
        .limit(100)
    )

Then, pass the constructed query to the clients ``search`` method,

.. code:: python

    async def main(query):
        client = XivApiClient()
        async for result in client.search(query):
            print(result.fields["Name"])
            print(result.fields["Description"])

    asyncio.run(main(query))


For information on other available methods, please refer to the documentation page:
https://xivapi2.readthedocs.io/en/latest/