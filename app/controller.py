import asyncio
import time
from datetime import datetime, timedelta, time as datetime_time
from .database import save_state, log_error, get_current_humidity
from .shelly import set_state, get_state
from .database import get_latest_humidity, get_current_electricity_price, save_humidity
from .electricity import fetch_electricity_price
from .state import app

"""
The controller plays different roles in a server-included or a server-based context.
Server-included: determine_state runs once on startup. After this point, the server receives its readouts exclusively from the associated microcomputer.
Server-based: The server runs its own loop, calling price API and receiving humidity readouts only from the associated microcomputer. 
"""

MIN_HUMIDITY = 45
# MAX_HUMIDITY = 55 ikke nyttig?
EMERGENCY_THRESHOLD = 70

DARK_TIME_SLEEP = 22
DARK_TIME_WAKE = 6

SHELLY_RESTART_DELAY = 900  # 15 minutes


async def determine_state(humidity, electricity_price):

    threshold = app.state.threshold

    current_state = await get_state()

    # humidity is below minimum threshold and switches off
    if humidity <= MIN_HUMIDITY:
        desired_state = False
        reason = f"Humidity {humidity}% below minimum threshold " f"{MIN_HUMIDITY}%"

    # humidity is above emergency threshold and runs regardless of price
    elif humidity >= EMERGENCY_THRESHOLD:
        desired_state = True
        reason = (
            f"Emergency threshold crossed: humidity {humidity}% >= "
            f"{EMERGENCY_THRESHOLD}%"
        )

    # humidity is between minimum and maximum threshold, operates normally
    elif humidity >= MIN_HUMIDITY and humidity < EMERGENCY_THRESHOLD:
        if electricity_price <= threshold:
            desired_state = True
            reason = (
                f"Humidity {humidity}% is within range, and "
                f"electricity price {electricity_price} DKK/kWh "
                f"is below threshold {threshold} DKK/kWh"
            )
        else:
            desired_state = False
            reason = (
                f"Humidity {humidity}% within range, but "
                f"electricity price {electricity_price} DKK/kWh "
                f"is above threshold {threshold} DKK/kWh"
            )

    else:
        desired_state = electricity_price <= threshold

        if desired_state:
            reason = (
                f"Humidity {humidity}% is between minimum and maximum "
                f"thresholds and electricity price {electricity_price} "
                f"DKK/kWh is below threshold {threshold} DKK/kWh"
            )
        else:
            reason = (
                f"Humidity {humidity}% is between minimum and maximum "
                f"thresholds and electricity price {electricity_price} "
                f"DKK/kWh is above threshold {threshold} DKK/kWh"
            )
    # compressor lockout prevents the dehumidifier from restarting for 15 minutes after being switched off
    if (
        not current_state
        and desired_state
        and app.state.shelly_off_timestamp is not None
    ):
        elapsed = time.monotonic() - app.state.shelly_off_timestamp

        if elapsed < SHELLY_RESTART_DELAY:
            desired_state = False
            remaining = SHELLY_RESTART_DELAY - elapsed
            reason = f"Compressor lockout active: " f"{remaining:.0f} seconds remaining"

    # sets dark time, within which the plug will never switch on
    current_time = datetime.now().time()
    dark_time = current_time >= datetime_time(
        DARK_TIME_SLEEP, 0
    ) or current_time < datetime_time(DARK_TIME_WAKE, 0)

    if dark_time:
        desired_state = False
        reason = (
            f"Dark time active: current time {current_time.strftime('%H:%M')}"
            f"is between 22:00 and 06:00"
        )

    print(
        f"Humidity: {humidity}% | "
        f"Electricity: {electricity_price} DKK/kWh | "
        f"Threshold: {threshold} DKK/kWh | "
        f"Current state: {'ON' if current_state else 'OFF'} | "
        f"Desired state: {'ON' if desired_state else 'OFF'}"
    )

    print(f"Reason: {reason}")

    if desired_state != current_state:
        print("Changing Shelly state...")

        shelly_result = await set_state(desired_state)

        print(f"set_state returned: {shelly_result!r}")

        if shelly_result:
            await save_state(desired_state, reason)

            print(
                f"TURNED "
                f"{'ON' if desired_state else 'OFF'}: "
                f"{reason}"
            )
        else:
            print("Failed to change Shelly state.")

    return {
        "humidity": humidity,
        "electricity_price": electricity_price,
        "threshold": threshold,
        "current_state": current_state,
        "desired_state": desired_state,
        "reason": reason,
    }

# allows continuous operation even if electricity price API is not available
async def determine_state_without_price(humidity):
    current_state = await get_state()

    if humidity <= MIN_HUMIDITY:
        desired_state = False
        reason = (
            f"Humidity {humidity}% is below minimum threshold "
            f"{MIN_HUMIDITY}%; no electricity price available"
        )

    elif humidity >= EMERGENCY_THRESHOLD: 
        desired_state = True
        reason = (
            f"Emergency threshold crossed: humidity {humidity}% >= "
            f"{EMERGENCY_THRESHOLD}%; no electricity price available"
        )

    else:
        desired_state = False
        reason = (
            f"No electricity price available; "
            f"humidity {humidity}% does not require emergency operation"
        )

    return {
        "humidity": humidity,
        "electricity_price": None,
        "threshold": app.state.threshold,
        "current_state": current_state,
        "desired_state": desired_state,
        "reason": reason,
    }

server_based_task = None

# describes a loop for electricity price retrieval in a server-based context; not relevant in a server-inclusive context
async def server_based_loop():
    while True:
        try:
            # freshest sensor from the DB (not the GPIO pin)
            humidity, source = await get_current_humidity()

            #  "blind = safe". If NO sensor has a fresh reading, humidity is
            #     None. We must NOT run the decision logic (comparing None would
            #     crash), so we force the plug OFF and wait for the next cycle.
            if humidity is None:
                print("No fresh humidity reading — safe mode (OFF).")
                if await get_state():  # only act if it's ON
                    await set_state(False)
                    await save_state(False, "No fresh sensor data — safe OFF")

            else:
                # We HAVE a good reading -> run the normal price + decision flow.
                print(f"Using {source} reading: {humidity}%")

                price = None

                print("Retrieving current electricity price...")

                try:
                    price = await get_current_electricity_price()
                except Exception as e:
                    await log_error(e)
                    print("Retrieving electricity price from database has failed.")

                if price is None:
                    print("No electricity prices found in database. Fetching prices...")

                    try:
                        await fetch_electricity_price()
                    except Exception as e:
                        await log_error(e)
                        print(f"Electricity price fetch failed: {e}")

                    print("Retrying current electricity price retrieval...")
                    try:
                        price = await get_current_electricity_price()
                    except Exception as e:
                        await log_error(e)
                        print("Retry has failed.")

                if price is None:
                    print("Running without API data.")
                    result = await determine_state_without_price(humidity)

                else:
                    print(f"Price retrieved sucessfully: {price}")

                    result = await determine_state(
                        humidity,
                        price,
                    )

                    print(f"Price at timestamp {datetime.now()}: {price} DKK/kWh")

                if result["desired_state"] != result["current_state"]:
                    print("Changing Shelly state...")

                    shelly_result = await set_state(result["desired_state"])

                    print(f"set_state returned: {shelly_result!r}")

                    if shelly_result:
                        await save_state(result["desired_state"], result["reason"])

                        print(
                            f"TURNED "
                            f"{'ON' if result['desired_state'] else 'OFF'}: "
                            f"{result['reason']}"
                        )
                    else:
                        print("Failed to change Shelly state.")




        except Exception as e:
            await log_error(e)
            print(f"Server-based control failed: {e}")
            print(f"{type(e).__name__}: {repr(e)}")

        now = datetime.now()
        next_quarter = now.replace(second=0, microsecond=0) + timedelta(
            minutes=15 - (now.minute % 15)
        )

        await asyncio.sleep((next_quarter - now).total_seconds())


async def start_server_based_loop():

    global server_based_task

    if server_based_task is not None and not server_based_task.done():
        return False

    server_based_task = asyncio.create_task(server_based_loop())

    return True


async def stop_server_based_loop():

    global server_based_task

    if server_based_task is None:
        return False

    server_based_task.cancel()

    try:
        await server_based_task
    except asyncio.CancelledError as e:
        await log_error(e)
        pass

    server_based_task = None

    return True


async def dht11_feeder(interval=30, max_failures=5):
    """Reads the local DHT11 every `interval` seconds and saves it
    with source='dht11'. Only started when ENABLE_DHT11=true.
    Safety (from main): if the sensor fails max_failures times in a
    row, shut the plug off - a blind system must not keep running.
    """
    import board            # imported HERE (lazily), not at top of file, so
    import adafruit_dht     # machines without the sensor (home) never touch it
    dht = adafruit_dht.DHT11(board.D4)

    failures = 0
    while True:
        try:
            humidity = dht.humidity
            temperature = dht.temperature
            if humidity is not None and temperature is not None:
                await save_humidity(humidity, temperature, source="dht11")
                print(f"[dht11] {humidity:.1f}% {temperature:.1f}C")
                failures = 0
            else:
                failures += 1
        except RuntimeError as e:
            await log_error(e)      # DHT11 misreads often — just retry next cycle
            failures += 1
        except Exception as e:
            await log_error(e)
            failures += 1

        if failures >= max_failures:
            await set_state(False)
            await log_error(
                RuntimeError(f"DHT11 failed {failures} times in a row. Shutting off the plug."))
            failures = 0
        await asyncio.sleep(interval)