from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .controller import (
    MIN_HUMIDITY,
    EMERGENCY_THRESHOLD,
    DARK_TIME_SLEEP,
    DARK_TIME_WAKE,
    SHELLY_RESTART_DELAY,
)
from .database import (
    get_dashboard_latest_reading,
    get_dashboard_humidity_history,
    get_dashboard_prices,
    get_dashboard_state_history,
    get_dashboard_errors,
    get_current_electricity_price,
)
from .shelly import get_state
from .state import app


PAGES_DIR = Path(__file__).resolve().parent / "pages"

router = APIRouter(prefix="/dashboard")


@router.get("/", response_class=HTMLResponse)
async def dashboard_page():
    html = (PAGES_DIR / "dashboard.html").read_text(
        encoding="utf-8"
    )

    return HTMLResponse(
        content=html,
        media_type="text/html; charset=utf-8",
    )


@router.get("/api/status")
async def dashboard_status():
    latest = await get_dashboard_latest_reading()

    try:
        price = await get_current_electricity_price()
    except Exception:
        price = None

    try:
        shelly_state = await get_state()
        shelly_reachable = True
    except Exception:
        shelly_state = None
        shelly_reachable = False

    threshold = getattr(
        app.state,
        "threshold",
        None,
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "latest": latest,
        "electricity_price": price,
        "electricity_threshold": threshold,
        "shelly": {
            "reachable": shelly_reachable,
            "state": shelly_state,
        },
        "control": {
            "minimum_humidity": MIN_HUMIDITY,
            "emergency_humidity": EMERGENCY_THRESHOLD,
            "dark_time_sleep": DARK_TIME_SLEEP,
            "dark_time_wake": DARK_TIME_WAKE,
            "restart_delay": SHELLY_RESTART_DELAY,
        },
    }


@router.get("/api/history")
async def dashboard_history(hours: int = 24):
    hours = max(1, min(hours, 168))

    return {
        "hours": hours,
        "readings": await get_dashboard_humidity_history(
            hours
        ),
    }


@router.get("/api/prices")
async def dashboard_prices():
    return {
        "threshold": getattr(
            app.state,
            "threshold",
            None,
        ),
        "prices": await get_dashboard_prices(),
    }


@router.get("/api/states")
async def dashboard_states(limit: int = 20):
    limit = max(1, min(limit, 100))

    return {
        "states": await get_dashboard_state_history(
            limit
        ),
    }


@router.get("/api/errors")
async def dashboard_errors(limit: int = 10):
    limit = max(1, min(limit, 100))

    return {
        "errors": await get_dashboard_errors(
            limit
        ),
    }   