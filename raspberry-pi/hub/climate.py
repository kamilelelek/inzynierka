"""Cykliczny odczyt DHT22: walidacja, odrzucanie skoków, wygładzanie medianą."""

from __future__ import annotations

import logging
import statistics
import threading
from collections import deque
from typing import Callable

from hub.hardware import Dht22, DhtReadError, DhtReading

log = logging.getLogger(__name__)

# Zakres pomiarowy DHT22 z dokumentacji producenta.
TEMPERATURE_RANGE_C = (-40.0, 80.0)
HUMIDITY_RANGE = (0.0, 100.0)
# Większa zmiana między kolejnymi odczytami jest traktowana jako błąd czujnika...
MAX_TEMPERATURE_STEP_C = 5.0
MAX_HUMIDITY_STEP = 20.0
# ...chyba że powtórzy się tyle razy z rzędu. Wtedy to prawdziwa zmiana, a nie zakłócenie.
SPIKE_CONFIRMATIONS = 3
MEDIAN_WINDOW = 3


class ReadingFilter:
    """Odrzuca odczyty spoza zakresu i pojedyncze skoki, wygładza medianą z ostatnich odczytów."""

    def __init__(self) -> None:
        self._window: deque[DhtReading] = deque(maxlen=MEDIAN_WINDOW)
        self._spikes_in_row = 0

    def validate(self, reading: DhtReading) -> str | None:
        """Zwraca powód odrzucenia albo None, jeśli odczyt jest poprawny (wtedy trafia do okna)."""
        t, h = reading.temperature, reading.humidity
        if not TEMPERATURE_RANGE_C[0] <= t <= TEMPERATURE_RANGE_C[1]:
            return f"temperatura poza zakresem: {t}"
        if not HUMIDITY_RANGE[0] <= h <= HUMIDITY_RANGE[1]:
            return f"wilgotność poza zakresem: {h}"

        if self._window:
            last = self._window[-1]
            if abs(t - last.temperature) > MAX_TEMPERATURE_STEP_C or abs(h - last.humidity) > MAX_HUMIDITY_STEP:
                self._spikes_in_row += 1
                if self._spikes_in_row < SPIKE_CONFIRMATIONS:
                    return f"skok wartości ({last.temperature} -> {t} °C, {last.humidity} -> {h} %)"
                log.info("Skok potwierdzony %d razy, przyjmuję nową wartość bazową", SPIKE_CONFIRMATIONS)
                self._window.clear()

        self._spikes_in_row = 0
        self._window.append(reading)
        return None

    def smoothed(self) -> DhtReading:
        return DhtReading(
            temperature=round(statistics.median(r.temperature for r in self._window), 1),
            humidity=round(statistics.median(r.humidity for r in self._window), 1),
        )


class ClimateMonitor:
    """Wątek odczytujący czujnik co interval_s.

    on_valid dostaje surowy, zwalidowany odczyt (fail-safe reaguje bez opóźnienia mediany),
    publish dostaje odczyt wygładzony.
    """

    def __init__(
        self,
        sensor: Dht22,
        interval_s: float,
        publish: Callable[[DhtReading], None],
        on_valid: Callable[[DhtReading], None],
        on_invalid: Callable[[], None],
    ) -> None:
        self._sensor = sensor
        self._interval_s = interval_s
        self._publish = publish
        self._on_valid = on_valid
        self._on_invalid = on_invalid
        self._filter = ReadingFilter()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="climate", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=self._interval_s + 5)

    def _run(self) -> None:
        while True:
            try:
                self.read_once()
            except Exception:
                # Nieprzewidziany błąd nie może zatrzymać pętli: liczymy go jak błędny odczyt.
                log.exception("Nieoczekiwany błąd odczytu DHT22")
                self._on_invalid()
            if self._stop.wait(self._interval_s):
                return

    def read_once(self) -> None:
        try:
            reading = self._sensor.read()
        except DhtReadError as e:
            log.debug("Nieudany odczyt DHT22: %s", e)
            self._on_invalid()
            return

        rejection = self._filter.validate(reading)
        if rejection:
            log.warning("Odrzucono odczyt DHT22: %s", rejection)
            self._on_invalid()
            return

        self._on_valid(reading)
        self._publish(self._filter.smoothed())
