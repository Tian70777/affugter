import os
import httpx
import time
from .state import app
from dotenv import load_dotenv
from .database import log_error

load_dotenv()

SHELLY = os.getenv("SHELLY_HOST")

# determines HTTP contact with smart plug on local network
# local mDNS resolved hostname placed in .env
async def check_shelly():
    url = (
        f"http://{SHELLY}/rpc/Shelly.GetDeviceInfo"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)

        print(f"Shelly response: {response.status_code}")

        if response.status_code == 200:
            return True

        return False

    except Exception as e:
        await log_error(e)
        print(f"Shelly connection failed: {e}")
        return False

# sets state (on/off) of smart plug
async def set_state(state: bool):
    url = (
        f"http://{SHELLY}/rpc/Switch.Set"
        f"?id=0&on={'true' if state else 'false'}"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        if response.status_code == 200 and not state:
            app.state.shelly_off_timestamp = time.monotonic()

        return response.status_code == 200
    except Exception as e:
        await log_error(e)
        raise RuntimeError(
            f"Failed to retrieve current Shelly state: "
            f"{type(e).__name__}: {e!r}"
        ) from e
# retrieves current state (on/off) of smart plug
async def get_state():
    url = (
        f"http://{SHELLY}/rpc/Switch.GetStatus"
        "?id=0"
    )

    try: 
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
    except Exception as e:
        await log_error(e)
        raise RuntimeError(
            f"Failed to retrieve current Shelly state: "
            f"{type(e).__name__}: {e!r}"
        ) from e

    return response.json()["output"]