import os
import psycopg
import math
from datetime import datetime, timezone
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Europe/Copenhagen")

load_dotenv()

"""
Establishes connection to the associated database and inserts data received from Arduino and electricity price API
"""

async def get_connection():
    return await psycopg.AsyncConnection.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

async def log_error(error):
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO errors (error_type, error_message)
                VALUES (%s, %s)
                """,
                (type(error).__name__, str(error))
            )
        await conn.commit()


async def save_humidity(percent, temperature, source="dht11"):
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO Humidity (percent, temperature, source)
                VALUES (%s, %s, %s)
                """,
                (percent, temperature, source),
            )


async def get_latest_humidity():
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT percent
                FROM Humidity
                ORDER BY timestamp DESC
                LIMIT 1
                """)

            result = await cur.fetchone()

            if result is None:
                raise Exception("No humidity readings found")

            return float(result[0])


async def get_current_electricity_price():
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT DKK_per_kWh
                FROM Electricity_Prices
                WHERE NOW() >= time_start
                AND NOW() < time_end
                ORDER BY time_start DESC
                LIMIT 1
                """)

            result = await cur.fetchone()

            if result is None:
                raise Exception("No electricity price found for current time")

            return float(result[0])


async def save_electricity_price(dkk_per_kwh, time_start, time_end):
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO Electricity_Prices
                (
                    DKK_per_kWh,
                    time_start,
                    time_end
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (time_start, time_end)
                DO NOTHING
                """,
                (
                    dkk_per_kwh,
                    time_start,
                    time_end,
                ),
            )


async def save_state(state, reason):
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO Humidifier_State (state, reason)
                VALUES (%s, %s)
                """,
                (state, reason),
            )

# in a server-based context, retrieves 
async def get_daily_threshold(percentile=0.25):

    today = datetime.now(TIMEZONE).date()

    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:

            await cur.execute(
                """
                SELECT DKK_per_kWh
                FROM Electricity_Prices
                WHERE time_start::date = %s
                ORDER BY DKK_per_kWh
                """,
                (today,),
            )

            rows = await cur.fetchall()

    if len(rows) < 4 * 24:
        raise Exception(
            f"Expected at least 96 electricity prices for {today}, "
            f"but found only {len(rows)} in the database"
        )

    values = [
        float(row[0])
        for row in rows
    ]

    count = max(
        1,
        math.ceil(len(values) * percentile),
    )

    threshold = values[count - 1]

    print(f"Threshold calculation for {today}:")
    print(f"  Prices retrieved: {len(values)}")
    print(f"  Percentile: {percentile * 100:.0f}%")
    print(f"  Prices in lowest {percentile * 100:.0f}%: {count}")
    print(f"  Threshold index: {count - 1}")
    print(f"  Threshold: {threshold:.5f} DKK/kWh")

    print("  Sorted prices:")

    for index, value in enumerate(values):
        print(
            f"    {index}: {value:.5f} DKK/kWh"
        )

    return threshold

# How old a reading may be before we stop trusting it (seconds)
MAX_AGE = {"zigbee": 1800, "dht11": 180}   # zigbee sleeps; dht11 reports often
PRIORITY = ["zigbee", "dht11"]             # try zigbee first, then dht11


async def _latest_for_source(source):
    """Newest (percent, temperature, timestamp) for one source, or None."""
    conn = await get_connection()
    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT percent, temperature, timestamp
                FROM Humidity
                WHERE source = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (source,),
            )
            return await cur.fetchone()


async def get_current_humidity():
    """Pick the freshest trustworthy sensor.
    Returns (humidity, source) or (None, None) if everything is stale."""
    now = datetime.now(timezone.utc)
    for source in PRIORITY:
        row = await _latest_for_source(source)
        if row is None:
            continue                       # this sensor never reported -> skip
        percent, temperature, ts = row
        age = (now - ts).total_seconds()
        if age < MAX_AGE[source]:
            return float(percent), source  # fresh enough -> trust it!
    return None, None                      # nobody had a fresh reading

async def get_dashboard_latest_reading():
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    percent,
                    temperature,
                    timestamp
                FROM Humidity
                ORDER BY timestamp DESC
                LIMIT 1
                """
            )

            row = await cur.fetchone()

    if row is None:
        return None

    return {
        "humidity": float(row[0]),
        "temperature": (
            float(row[1])
            if row[1] is not None
            else None
        ),
        "timestamp": row[2].isoformat(),
    }


async def get_dashboard_humidity_history(hours=24):
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    percent,
                    temperature,
                    timestamp
                FROM Humidity
                WHERE timestamp >= NOW() - (%s * INTERVAL '1 hour')
                ORDER BY timestamp ASC
                """,
                (hours,),
            )

            rows = await cur.fetchall()

    return [
        {
            "humidity": float(row[0]),
            "temperature": (
                float(row[1])
                if row[1] is not None
                else None
            ),
            "timestamp": row[2].isoformat(),
        }
        for row in rows
    ]


async def get_dashboard_prices():
    today = datetime.now(TIMEZONE).date()

    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    DKK_per_kWh,
                    time_start,
                    time_end
                FROM Electricity_Prices
                WHERE time_start::date = %s
                ORDER BY time_start ASC
                """,
                (today,),
            )

            rows = await cur.fetchall()

    return [
        {
            "price": float(row[0]),
            "time_start": row[1].isoformat(),
            "time_end": row[2].isoformat(),
        }
        for row in rows
    ]


async def get_dashboard_state_history(limit=20):
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    state,
                    reason,
                    timestamp
                FROM Humidifier_State
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = await cur.fetchall()

    return [
        {
            "state": row[0],
            "reason": row[1],
            "timestamp": row[2].isoformat(),
        }
        for row in rows
    ]


async def get_dashboard_errors(limit=10):
    conn = await get_connection()

    async with conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    error_type,
                    error_message,
                    timestamp
                FROM Errors
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = await cur.fetchall()

    return [
        {
            "error_type": row[0],
            "error_message": row[1],
            "timestamp": row[2].isoformat(),
        }
        for row in rows
    ]