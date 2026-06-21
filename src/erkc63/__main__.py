import asyncio
import json
import logging
from typing import Mapping

from .client import ErkcClient

logging.basicConfig(level=logging.DEBUG)

with open("secrets.json") as f:
    secrets: Mapping[str, str] = json.load(f)


async def main():
    async with ErkcClient(secrets["login"], secrets["password"]) as cli:
        print(await cli.account_info())
        print(await cli.meters_info())

        for m in await cli.meters_history():
            for value in m.values:
                print(value)

        dd = await cli.year_accruals(include_details=True)

        for payment in dd:
            print(payment)
            await cli.download_payment_data(payment)

        for x in await cli.accruals_history():
            print(x)

        for x in await cli.payments_history():
            print(x)


asyncio.run(main())
