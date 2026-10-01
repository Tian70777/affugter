from fastapi import APIRouter

from .database import (
    save_humidity,
    save_electricity_price,
    save_state,
)
from .models import (
    HumidityReading,
    ElectricityPriceReading,
    ShellyState,
)
from datetime import datetime

router = APIRouter()

'''
Hosts endpoints for retrieval of sensor data and electricity prices
Any changes in the state of the Shelly plug are also logged with reasoning and saved in the database
'''

@router.post("/humidity")
async def receive_humidity(data: HumidityReading):
    print(
        f"Humidity: {data.humidity}% "
        f"Temperature: {data.temperature} C "
        f"Timestamp: {datetime.now()}"
    )

    await save_humidity(data.humidity, data.temperature)

    return {"status": "ok"}


@router.post("/electricity-price")
async def receive_electricity_price(data: ElectricityPriceReading):
    print(
        f"Electricity price: {data.dkk_per_kwh:.5f} DKK/kWh "
        f"Threshold: {data.threshold:.5f} DKK/kWh "
        f"Period: {data.time_start} - {data.time_end}"
    )

    await save_electricity_price(
        data.dkk_per_kwh, data.time_start, data.time_end
    )

    return {"status": "ok"}


@router.post("/humidifier-state")
async def receive_humidifier_state(data: ShellyState):
    print(
        f"Humidifier: {'ON' if data.state else 'OFF'} "
        f"Reason: {data.reason} "
        f"Timestamp: {datetime.now()}"
    )

    print(f"Shelly plug is: {'On' if data.state else 'Off'}")
    print(f"Reason: {data.reason}")

    await save_state(data.state, data.reason)

    return {"status": "ok"}
