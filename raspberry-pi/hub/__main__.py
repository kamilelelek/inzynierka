"""Punkt wejścia huba: python -m hub"""

from __future__ import annotations

import logging
import signal
import sys
import threading
from typing import Callable

from hub.actuators import HeaterController, LedController, parse_command
from hub.climate import ClimateMonitor
from hub.config import ConfigError, load_config
from hub.hardware import DhtReading, create_hardware
from hub.motion import MotionDetector
from hub.mqtt_client import QOS_RELIABLE, QOS_TELEMETRY, HubMqttClient, Topics, utc_now_iso

log = logging.getLogger("hub")


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


def command_handler(device: str, apply: Callable[[bool], None]) -> Callable[[bytes], None]:
    def handle(payload: bytes) -> None:
        on = parse_command(payload)
        if on is None:
            log.warning("Niepoprawna komenda dla %s: %r", device, payload)
            return
        apply(on)

    return handle


def main() -> int:
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Błąd konfiguracji: {e}", file=sys.stderr)
        return 2

    setup_logging(config.log_level)
    log.info("Start huba %s (mock GPIO: %s)", config.hub_id, config.gpio.mock)

    stop_event = threading.Event()

    def handle_signal(signum, _frame) -> None:
        log.info("Otrzymano sygnał %s, zamykanie", signal.Signals(signum).name)
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)  # systemd stop

    topics = Topics.for_hub(config.hub_id)
    client = HubMqttClient(config.mqtt, topics)
    hardware = create_hardware(config.gpio)

    led = LedController(hardware.led_relay, lambda on: client.publish_device_state(topics.led_state, on))
    heater = HeaterController(
        hardware.heater_relay,
        config.heater,
        # Odczyt starszy niż max_invalid_readings + 1 cykli blokuje grzałkę (np. gdy wątek odczytu stanie).
        max_reading_age_s=config.dht_interval_s * (config.heater.max_invalid_readings + 1),
        publish_state=lambda on: client.publish_device_state(topics.heater_state, on),
    )
    motion = MotionDetector(
        config.motion_clear_s,
        lambda detected: client.publish_json(
            topics.motion_event, {"motion": detected, "ts": utc_now_iso()}, QOS_RELIABLE
        ),
    )

    def publish_climate(reading: DhtReading) -> None:
        client.publish_json(
            topics.climate_telemetry,
            {"temperature": reading.temperature, "humidity": reading.humidity, "ts": utc_now_iso()},
            QOS_TELEMETRY,
        )

    climate = ClimateMonitor(
        hardware.dht,
        config.dht_interval_s,
        publish=publish_climate,
        on_valid=lambda reading: heater.on_valid_reading(reading.temperature),
        on_invalid=heater.on_invalid_reading,
    )

    def on_connection_change(connected: bool) -> None:
        heater.on_connection_change(connected)
        if connected:
            led.publish_current()

    client.subscribe(topics.led_set, command_handler("led", led.handle_command))
    client.subscribe(topics.heater_set, command_handler("heater", heater.handle_command))
    client.add_connection_listener(on_connection_change)

    try:
        heater.start()
        climate.start()
        hardware.pir.start(motion.on_input)
        client.start()
        # Krótki timeout zamiast wait() bez limitu, żeby Ctrl+C działał też na Windows.
        while not stop_event.wait(1.0):
            pass
    finally:
        # Kolejność: najpierw wyłączyć przekaźniki i opublikować OFF, potem rozłączyć MQTT.
        climate.stop()
        motion.close()
        heater.shutdown()
        led.shutdown()
        client.stop()
        hardware.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
