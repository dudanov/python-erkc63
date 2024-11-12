import asyncio
import json
import logging

from .client import ErkcClient

logging.basicConfig(level=logging.DEBUG)

with open("secrets.json") as f:
    secrets: dict[str, str] = json.load(f)


async def main():
    async with ErkcClient(secrets["login"], secrets["password"]) as cli:
        print(await cli.account_info())
        print(await cli.meters_info())

        for m in await cli.meters_history():
            for value in m.history:
                print(value)

        for x in await cli.year_accruals(include_details=True):
            print(x)

        for x in await cli.accruals_history():
            print(x)

        for x in await cli.payments_history():
            print(x)


asyncio.run(main())
