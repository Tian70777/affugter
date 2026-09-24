# app/main.py

import asyncio
from contextlib import asynccontextmanager
from .state import app
from fastapi import FastAPI
from .sensors import router as sensor_router
from .debug_router import router as debug_router
from .shelly import check_shelly
from .electricity import fetch_electricity_price
from .database import get_daily_threshold, log_error
from .controller import server_based_loop
from app.dashboard import router as dashboard_router

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

    try:
        app.state.threshold = await get_daily_threshold()

        print(
            f"Today's threshold: "
            f"{app.state.threshold:.5f} DKK/kWh"
        )

    except Exception as e:
        await log_error(e)
        print(f"Threshold fetch failed: {e}")
        app.state.threshold = None

    server_based_task = asyncio.create_task(
        server_based_loop()
    )

    try:
        yield
    finally:
        pass


app.router.lifespan_context = lifespan

app.include_router(sensor_router)
app.include_router(debug_router)
app.include_router(dashboard_router)
