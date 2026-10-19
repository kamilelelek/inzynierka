"""Punkt wejścia huba: python -m hub"""

from __future__ import annotations

import logging
import signal
import sys
import threading

from hub.config import ConfigError, load_config
from hub.mqtt_client import HubMqttClient, Topics

log = logging.getLogger("hub")


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


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

    client = HubMqttClient(config.mqtt, Topics.for_hub(config.hub_id))
    client.start()
    try:
        # Krótki timeout zamiast wait() bez limitu, żeby Ctrl+C działał też na Windows.
        while not stop_event.wait(1.0):
            pass
    finally:
        client.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
