# app/electricity.py

import httpx
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .database import save_electricity_price
from .models import ElectricityPrice


VAT_MULTIPLIER = 1.25
TIMEZONE = ZoneInfo("Europe/Copenhagen")


async def fetch_electricity_price():

    now = datetime.now(TIMEZONE)
    today = now.date()
    tomorrow = today + timedelta(days=1)

    url = "https://api.energidataservice.dk/dataset/DayAheadPrices"

    params = {
        "start": today.isoformat(),
        "end": tomorrow.isoformat(),
        "filter": '{"PriceArea":["DK2"]}',
        "columns": "TimeUTC,TimeDK,PriceArea,DayAheadPriceDKK",
        "sort": "TimeUTC",
        "limit": 0,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
        )

        response.raise_for_status()
        prices = response.json()["records"]

    if len(prices) < 4 * 24:
        raise Exception(
            f"Expected at least 96 DK2 electricity prices for {today}, "
            f"but received {len(prices)}"
        )

    for price in prices:

        time_start = datetime.fromisoformat(
            price["TimeUTC"]
        ).replace(
            tzinfo=ZoneInfo("UTC")
        ).astimezone(TIMEZONE)

        time_end = time_start + timedelta(minutes=15)

        dkk_per_kwh = (
            float(price["DayAheadPriceDKK"]) / 1000
        )

        await save_electricity_price(
            dkk_per_kwh,
            time_start,
            time_end,
        )

        if time_start <= now < time_end:
            current_price = ElectricityPrice(
                dkk_per_kwh=dkk_per_kwh,
                time_start=time_start,
                time_end=time_end,
            )

    if "current_price" not in locals():
        raise Exception("No current electricity price found")

    return current_price


if __name__ == "__main__":
    import asyncio

    asyncio.run(fetch_electricity_price())
