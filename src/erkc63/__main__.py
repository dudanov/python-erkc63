import asyncio
import json
import logging

from .client import ErkcClient

logging.basicConfig(level=logging.DEBUG)

with open("secrets.json") as f:
    secrets: dict[str, str] = json.load(f)


async def main():
    async with ErkcClient(secrets["login"], secrets["password"]) as cli:
        # print(await cli.account_info())
        # print(await cli.meters_info())

        # for m in await cli.meters_history():
        #    for value in m.history:
        #        print(value)

        # x = await cli.year_accruals(include_details=True)

        # await cli.qr_codes(x[1])
        dd = await cli.meters_history()
        for meter in dd:
            print(meter.name, meter.serial)
            for value in meter.history:
                print(
                    f"  {value.date} {value.value} {value.consumption} {value.source}"
                )


#        for x in await cli.accruals_history():
#            print(x)

#        for x in await cli.payments_history():
#            print(x)


asyncio.run(main())
