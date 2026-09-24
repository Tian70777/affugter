
from .database import (
    save_state,
    get_latest_humidity,
    get_current_electricity_price,
)
from .controller import determine_state, start_server_based_loop, stop_server_based_loop
from .shelly import set_state
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

PAGES_DIR = Path(__file__).resolve().parent / "pages"

router = APIRouter(prefix="/debug")

@router.get("/", response_class=HTMLResponse)
async def debug_page():
    return (PAGES_DIR / "debug.html").read_text()

'''
Endpoints for debugging
Each test is described in `tests.py`
Called from venv with 'python -m app.tests <test> <value>'
'''

@router.post("/test/high_price")
async def test_high_price():
    humidity = await get_latest_humidity()

    result = await determine_state(
        humidity=humidity,
        electricity_price=100,
    )

    return result


@router.post("/test/low_price")
async def test_low_price():
    humidity = await get_latest_humidity()

    result = await determine_state(
        humidity=humidity,
        electricity_price=0.10,
    )

    return result

@router.post("/test/humidity/{val}")
async def test_low_price(val: int):
    electricity_price = await get_current_electricity_price()
    humidity = val

    result = await determine_state(
        humidity=humidity,
        electricity_price=electricity_price,
    )

    return result

@router.post("/test/price/{val}")
async def test_low_price(val: float):
    electricity_price = val
    humidity = await get_latest_humidity()

    result = await determine_state(
        humidity=humidity,
        electricity_price=electricity_price,
    )

    return result

@router.post("/test/custom/{hum}/{price}")
async def test_custom(hum: int, price: float):
    result = await determine_state(
        humidity=hum,
        electricity_price=price,
    )

    return result


@router.post("/test/high_humidity")
async def test_high_humidity():
    electricity_price = await get_current_electricity_price()

    result = await determine_state(
        humidity=100,
        electricity_price=electricity_price,
    )

    return result


@router.post("/test/low_humidity")
async def test_low_humidity():
    electricity_price = await get_current_electricity_price()

    result = await determine_state(
        humidity=0,
        electricity_price=electricity_price,
    )

    return result


@router.post("/test/real")
async def test_real():
    humidity = await get_latest_humidity()
    electricity_price = await get_current_electricity_price()

    result = await determine_state(
        humidity=humidity,
        electricity_price=electricity_price,
    )

    return result


@router.post("/test/on")
async def test_on():
    if await set_state(True):
        await save_state(True, "Testing")
        return {"status": "ok"}

    return {"status": "failed"}


@router.post("/test/off")
async def test_off():
    if await set_state(False):
        await save_state(False, "Testing")
        return {"status": "ok"}

    return {"status": "failed"}

@router.post("/test/server_based")
async def test_server_based():
    started = await start_server_based_loop()

    return {
        "status": "started" if started else "already_running"
    }


@router.post("/test/server_based/stop")
async def stop_server_based():
    stopped = await stop_server_based_loop()

    return {
        "status": "stopped" if stopped else "not_running"
    }