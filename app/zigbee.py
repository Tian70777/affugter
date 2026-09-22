"""Listens to Zigbee2MQTT and saves humidity readings as source='zigbee'."""
import asyncio
import json
import os

import aiomqtt

from .database import save_humidity, log_error

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = 1883
TOPIC = "zigbee2mqtt/+"          # + = any single device under zigbee2mqtt/


async def _handle(message):
    """Turn one MQTT message into a saved reading (or ignore it)."""
    try:
        data = json.loads(message.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return                                  # not valid JSON -> ignore
    if not isinstance(data, dict) or "humidity" not in data:
        return                                  # no humidity in it -> ignore

    await save_humidity(
        data.get("humidity"),
        data.get("temperature"),
        source="zigbee",                        # <- the stamp!
    )
    print(f"[zigbee] {data.get('humidity')}% {data.get('temperature')}C")


async def listen_zigbee():
    """Runs forever: connect, listen, and reconnect if the link drops."""
    while True:
        try:
            async with aiomqtt.Client(MQTT_HOST, port=MQTT_PORT) as client:
                await client.subscribe(TOPIC)
                async for message in client.messages:
                    await _handle(message)
        except aiomqtt.MqttError as e:
            await log_error(e)
            print(f"[zigbee] connection lost, retrying in 5s: {e}")
            await asyncio.sleep(5)