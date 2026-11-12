"""Warstwa sprzętowa: prawdziwe GPIO (gpiozero, adafruit_dht) albo symulacja (tryb mock).

Biblioteki GPIO są importowane dopiero przy tworzeniu prawdziwych urządzeń,
dzięki czemu tryb mock działa na Windows bez ich instalowania.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from hub.config import GpioConfig

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DhtReading:
    temperature: float
    humidity: float


class DhtReadError(Exception):
    """Nieudany odczyt DHT22 (błąd sumy kontrolnej, timeout, brak danych)."""


class Relay(Protocol):
    name: str

    @property
    def is_on(self) -> bool: ...

    def set(self, on: bool) -> None: ...

    def close(self) -> None: ...


class Dht22(Protocol):
    def read(self) -> DhtReading:
        """Zwraca odczyt albo rzuca DhtReadError."""
        ...

    def close(self) -> None: ...


class PirInput(Protocol):
    def start(self, on_change: Callable[[bool], None]) -> None:
        """Wywołuje on_change(True/False) przy każdej zmianie stanu wyjścia czujnika."""
        ...

    def close(self) -> None: ...


# --- Prawdziwy sprzęt ---------------------------------------------------------


class GpioRelay:
    """Kanał modułu przekaźników sterowany stanem niskim (active-low)."""

    def __init__(self, name: str, pin: int) -> None:
        from gpiozero import OutputDevice

        self.name = name
        self._device = OutputDevice(pin, active_high=False, initial_value=False)

    @property
    def is_on(self) -> bool:
        return bool(self._device.value)

    def set(self, on: bool) -> None:
        if on:
            self._device.on()
        else:
            self._device.off()

    def close(self) -> None:
        self._device.off()
        self._device.close()


class GpioDht22:
    def __init__(self, pin: int) -> None:
        import adafruit_dht
        import board

        self._device = adafruit_dht.DHT22(getattr(board, f"D{pin}"))

    def read(self) -> DhtReading:
        try:
            temperature = self._device.temperature
            humidity = self._device.humidity
        except RuntimeError as e:  # tak adafruit_dht zgłasza typowe błędy odczytu
            raise DhtReadError(str(e)) from e
        if temperature is None or humidity is None:
            raise DhtReadError("czujnik nie zwrócił danych")
        return DhtReading(float(temperature), float(humidity))

    def close(self) -> None:
        self._device.exit()


class GpioPir:
    """Wyjście PIR (HC-SR501 ma wyjście push-pull, więc bez podciągania)."""

    def __init__(self, pin: int) -> None:
        from gpiozero import DigitalInputDevice

        self._device = DigitalInputDevice(pin, pull_up=None, active_state=True)

    def start(self, on_change: Callable[[bool], None]) -> None:
        self._device.when_activated = lambda: on_change(True)
        self._device.when_deactivated = lambda: on_change(False)
        if self._device.is_active:
            on_change(True)

    def close(self) -> None:
        self._device.close()


# --- Symulacja (GPIO_MOCK=true) -------------------------------------------------


class MockRelay:
    def __init__(self, name: str) -> None:
        self.name = name
        self._on = False

    @property
    def is_on(self) -> bool:
        return self._on

    def set(self, on: bool) -> None:
        if on != self._on:
            log.info("[MOCK] przekaźnik %s: %s", self.name, "ON" if on else "OFF")
        self._on = on

    def close(self) -> None:
        self.set(False)


class MockDht22:
    """Temperatura rośnie przy włączonej grzałce i wraca do otoczenia po wyłączeniu.

    Część odczytów celowo kończy się błędem, żeby sprawdzić filtrowanie i fail-safe.
    """

    HEATING_RATE_C_PER_S = 0.05  # +3 °C/min
    COOLING_FACTOR_PER_S = 0.01
    FAILURE_RATE = 0.05

    def __init__(self, heater_is_on: Callable[[], bool], ambient_c: float = 21.0) -> None:
        self._heater_is_on = heater_is_on
        self._ambient = ambient_c
        self._temperature = ambient_c
        self._humidity = 45.0
        self._last = time.monotonic()

    def read(self) -> DhtReading:
        now = time.monotonic()
        dt, self._last = now - self._last, now
        if self._heater_is_on():
            self._temperature += self.HEATING_RATE_C_PER_S * dt
        else:
            self._temperature += (self._ambient - self._temperature) * min(1.0, self.COOLING_FACTOR_PER_S * dt)
        self._temperature += random.gauss(0, 0.05)
        self._humidity = min(70.0, max(30.0, self._humidity + random.gauss(0, 0.3)))

        if random.random() < self.FAILURE_RATE:
            raise DhtReadError("[MOCK] symulowany błąd sumy kontrolnej")
        return DhtReading(round(self._temperature, 1), round(self._humidity, 1))

    def close(self) -> None:
        pass


class MockPir:
    """Co 20-60 s symuluje ruch trwający kilka sekund, czasem z krótkim zakłóceniem po nim."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, on_change: Callable[[bool], None]) -> None:
        self._thread = threading.Thread(target=self._run, args=(on_change,), name="mock-pir", daemon=True)
        self._thread.start()

    def _run(self, on_change: Callable[[bool], None]) -> None:
        while not self._stop.wait(random.uniform(20, 60)):
            on_change(True)
            if self._stop.wait(random.uniform(3, 8)):
                return
            on_change(False)
            # Krótki impuls tuż po ruchu: filtr w MotionDetector powinien go połknąć.
            if random.random() < 0.5 and not self._stop.wait(0.5):
                on_change(True)
                if self._stop.wait(0.3):
                    return
                on_change(False)

    def close(self) -> None:
        self._stop.set()


# --- Fabryka --------------------------------------------------------------------


@dataclass
class Hardware:
    led_relay: Relay
    heater_relay: Relay
    dht: Dht22
    pir: PirInput

    def close(self) -> None:
        # Najpierw przekaźniki: wyłączenie grzałki jest najważniejsze.
        for device in (self.heater_relay, self.led_relay, self.pir, self.dht):
            try:
                device.close()
            except Exception:
                log.exception("Błąd przy zamykaniu %s", type(device).__name__)


def create_hardware(gpio: GpioConfig) -> Hardware:
    if gpio.mock:
        log.warning("Tryb MOCK: GPIO nie jest używane, odczyty są symulowane")
        heater = MockRelay("heater")
        return Hardware(MockRelay("led"), heater, MockDht22(lambda: heater.is_on), MockPir())

    return Hardware(
        led_relay=GpioRelay("led", gpio.led_relay_pin),
        heater_relay=GpioRelay("heater", gpio.heater_relay_pin),
        dht=GpioDht22(gpio.dht_pin),
        pir=GpioPir(gpio.pir_pin),
    )
