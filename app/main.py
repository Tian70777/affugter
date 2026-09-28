# app/main.py
import os
import asyncio
from contextlib import asynccontextmanager
from .state import app
from fastapi import FastAPI
from .sensors import router as sensor_router
from .debug_router import router as debug_router
from .shelly import check_shelly
from .electricity import fetch_electricity_price
from .database import get_daily_threshold, log_error
from .controller import server_based_loop, dht11_feeder, refresh_threshold_if_needed
from .zigbee import listen_zigbee
from .dashboard_router import router as dashboard_router

"""
App lifespan
Retrieves electricity price on startup and calculates lowest 25% threshold (daily threshold)
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await check_shelly()
    except Exception as e:
        await log_error(e)
        print(f"Shelly connection failed: {e}")

    try:
        await fetch_electricity_price()

    except Exception as e:
        await log_error(e)
        print(f"Energi Data Service electricity price fetch failed: {e}")

    await refresh_threshold_if_needed()

    server_based_task = asyncio.create_task(
        server_based_loop()
    )
    # start only the sensor feeders THIS location has (from its .env)
    if os.getenv("ENABLE_ZIGBEE", "false").lower() == "true":
        asyncio.create_task(listen_zigbee())
        print("Zigbee catcher started.")

    if os.getenv("ENABLE_DHT11", "false").lower() == "true":
        asyncio.create_task(dht11_feeder())
        print("DHT11 feeder started.")

    try:
        yield
    finally:
        pass


app.router.lifespan_context = lifespan

app.include_router(sensor_router)
app.include_router(debug_router)
app.include_router(dashboard_router)
