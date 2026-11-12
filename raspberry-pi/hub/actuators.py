"""Sterowanie przekaźnikami: oświetlenie LED i grzałka z zabezpieczeniami (fail-safe)."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable

from hub.config import HeaterSafetyConfig
from hub.hardware import Relay

log = logging.getLogger(__name__)

# Po przekroczeniu progu grzałka może wrócić dopiero, gdy temperatura spadnie o tyle stopni.
SAFETY_HYSTERESIS_C = 1.0
WATCHDOG_PERIOD_S = 1.0


def parse_command(payload: bytes) -> bool | None:
    """{"state":"ON"} -> True, {"state":"OFF"} -> False, cokolwiek innego -> None."""
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        return None
    state = data.get("state") if isinstance(data, dict) else None
    if isinstance(state, str) and state.upper() in ("ON", "OFF"):
        return state.upper() == "ON"
    return None


class LedController:
    def __init__(self, relay: Relay, publish_state: Callable[[bool], None]) -> None:
        self._relay = relay
        self._publish_state = publish_state
        self._lock = threading.Lock()

    def handle_command(self, on: bool) -> None:
        with self._lock:
            self._relay.set(on)
            log.info("LED: %s", "ON" if on else "OFF")
            # Stan publikujemy zawsze, także bez zmiany: to potwierdzenie komendy dla backendu.
            self._publish_state(self._relay.is_on)

    def publish_current(self) -> None:
        with self._lock:
            self._publish_state(self._relay.is_on)

    def shutdown(self) -> None:
        with self._lock:
            self._relay.set(False)
            self._publish_state(False)


class HeaterController:
    """Grzałka jest włączona tylko wtedy, gdy spełnione są wszystkie warunki:

    - ostatnia komenda heater/set to ON i przyszła nie dawniej niż command_timeout_s (heartbeat),
    - jest połączenie z brokerem (rozłączenie kasuje komendę),
    - temperatura nie przekroczyła progu (powrót po spadku o SAFETY_HYSTERESIS_C),
    - ostatni poprawny odczyt DHT22 nie jest starszy niż max_reading_age_s
      i nie było max_invalid_readings błędnych odczytów z rzędu.
    """

    def __init__(
        self,
        relay: Relay,
        safety: HeaterSafetyConfig,
        max_reading_age_s: float,
        publish_state: Callable[[bool], None],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._relay = relay
        self._safety = safety
        self._max_reading_age_s = max_reading_age_s
        self._publish_state = publish_state
        self._clock = clock
        self._lock = threading.Lock()

        self._requested = False
        self._last_command_at = 0.0
        self._last_valid_reading_at: float | None = None
        self._invalid_in_row = 0
        self._over_temperature = False
        self._block_reason: str | None = None

        self._stop = threading.Event()
        self._watchdog = threading.Thread(target=self._watchdog_loop, name="heater-watchdog", daemon=True)

    @property
    def is_on(self) -> bool:
        return self._relay.is_on

    def start(self) -> None:
        self._watchdog.start()

    def handle_command(self, on: bool) -> None:
        with self._lock:
            self._requested = on
            self._last_command_at = self._clock()
            self._apply(publish_always=True)

    def on_valid_reading(self, temperature_c: float) -> None:
        with self._lock:
            self._last_valid_reading_at = self._clock()
            self._invalid_in_row = 0
            limit = self._safety.max_temperature_c
            if temperature_c > limit:
                self._over_temperature = True
            elif self._over_temperature and temperature_c <= limit - SAFETY_HYSTERESIS_C:
                self._over_temperature = False
            self._apply()

    def on_invalid_reading(self) -> None:
        with self._lock:
            self._invalid_in_row += 1
            self._apply()

    def on_connection_change(self, connected: bool) -> None:
        with self._lock:
            if connected:
                self._publish_state(self._relay.is_on)
                return
            if self._requested:
                log.warning("Grzałka: utracono połączenie z brokerem, kasuję komendę ON")
            self._requested = False
            self._apply()

    def check_timeouts(self) -> None:
        """Wywoływane cyklicznie przez watchdog; publiczne, żeby dało się testować bez wątku."""
        with self._lock:
            if self._requested and self._clock() - self._last_command_at > self._safety.command_timeout_s:
                log.warning(
                    "Grzałka: brak komendy heater/set przez %.0f s, wyłączam", self._safety.command_timeout_s
                )
                self._requested = False
            self._apply()

    def shutdown(self) -> None:
        self._stop.set()
        if self._watchdog.is_alive():
            self._watchdog.join(timeout=WATCHDOG_PERIOD_S * 2)
        with self._lock:
            self._requested = False
            self._relay.set(False)
            self._publish_state(False)

    def _watchdog_loop(self) -> None:
        while not self._stop.wait(WATCHDOG_PERIOD_S):
            try:
                self.check_timeouts()
            except Exception:
                log.exception("Błąd watchdoga grzałki")
                self._relay.set(False)

    def _current_block_reason(self) -> str | None:
        if self._over_temperature:
            return f"temperatura powyżej {self._safety.max_temperature_c} °C"
        if self._invalid_in_row >= self._safety.max_invalid_readings:
            return f"{self._invalid_in_row} błędnych odczytów DHT22 z rzędu"
        if self._last_valid_reading_at is None:
            return "brak poprawnego odczytu temperatury"
        if self._clock() - self._last_valid_reading_at > self._max_reading_age_s:
            return "nieaktualny odczyt temperatury"
        return None

    def _apply(self, publish_always: bool = False) -> None:
        """Wylicza stan docelowy i przełącza przekaźnik. Wywoływać pod self._lock."""
        reason = self._current_block_reason()
        if reason != self._block_reason:
            if reason:
                log.warning("Grzałka zablokowana: %s", reason)
            else:
                log.info("Grzałka odblokowana")
            self._block_reason = reason

        target = self._requested and reason is None
        if target != self._relay.is_on:
            self._relay.set(target)
            log.info("Grzałka: %s", "ON" if target else "OFF")
            self._publish_state(target)
        elif publish_always:
            self._publish_state(target)
