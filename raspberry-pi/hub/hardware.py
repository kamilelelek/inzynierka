"""Warstwa sprzętowa: prawdziwe GPIO (gpiozero, lgpio) albo symulacja (tryb mock).

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


# Protokół DHT22: host ściąga linię w dół na >= 1 ms, potem czujnik odpowiada (80 us L + 80 us H)
# i nadaje 40 bitów. Każdy bit to 50 us stanu niskiego i 26-28 us (0) albo 70 us (1) stanu wysokiego,
# więc odstęp między kolejnymi zboczami opadającymi wynosi ~76 us dla 0 i ~120 us dla 1.
DHT22_START_LOW_S = 0.002
DHT22_TRANSMISSION_S = 0.010
DHT22_BITS = 40
DHT22_BIT_THRESHOLD_NS = 100_000
# Wilgotność <= 100,0 % to wartość <= 1000 (0x03E8), więc 6 najstarszych bitów ramki jest zawsze zerami.
# Pozwala to odtworzyć do 6 początkowych bitów, gdy przełączenie linii w tryb alert spóźni się
# na pierwsze zbocza (na Pi 4 gubimy zwykle 1-3); błędną rekonstrukcję wyłapie suma kontrolna.
DHT22_MAX_MISSING_LEADING_BITS = 6


def decode_dht22(falling_edges_ns: list[int]) -> DhtReading:
    """Dekoduje odczyt ze znaczników czasu zboczy opadających (ns).

    Bierze ostatnie 41 zboczy: początki 40 bitów i koniec ostatniego bitu, więc pominięcie
    zbocza odpowiedzi czujnika (np. przez opóźnienie przełączenia linii) nie przeszkadza.
    Jeśli zgubiono też początki pierwszych bitów, uzupełnia je zerami
    (patrz DHT22_MAX_MISSING_LEADING_BITS).
    """
    min_edges = DHT22_BITS + 1 - DHT22_MAX_MISSING_LEADING_BITS
    if len(falling_edges_ns) < min_edges:
        raise DhtReadError(f"za mało zboczy: {len(falling_edges_ns)} (min. {min_edges})")
    edges = falling_edges_ns[-(DHT22_BITS + 1):]
    bits = [1 if b - a > DHT22_BIT_THRESHOLD_NS else 0 for a, b in zip(edges, edges[1:])]
    bits = [0] * (DHT22_BITS - len(bits)) + bits

    data = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, DHT22_BITS, 8)]
    if (sum(data[:4]) & 0xFF) != data[4]:
        raise DhtReadError(f"błędna suma kontrolna: {data}")
    if not any(data):
        raise DhtReadError("same zera (brak odpowiedzi czujnika?)")

    humidity = ((data[0] << 8) | data[1]) / 10
    temperature = (((data[2] & 0x7F) << 8) | data[3]) / 10
    if data[2] & 0x80:
        temperature = -temperature
    return DhtReading(temperature, humidity)


class GpioDht22:
    """Odczyt DHT22 przez lgpio: znaczniki czasu zboczy pochodzą z jądra, nie z pętli w Pythonie."""

    GPIO_CHIP = 0  # Raspberry Pi 4: gpiochip0

    def __init__(self, pin: int) -> None:
        import lgpio

        self._lg = lgpio
        self._pin = pin
        self._handle = lgpio.gpiochip_open(self.GPIO_CHIP)
        self._edges: list[int] = []
        # Callback rejestrujemy raz; zdarzenia przychodzą tylko, gdy linia jest w trybie alert.
        self._callback = lgpio.callback(
            self._handle, pin, lgpio.FALLING_EDGE, lambda chip, gpio, level, tick: self._edges.append(tick)
        )
        lgpio.gpio_claim_input(self._handle, pin, lgpio.SET_PULL_UP)

    def read(self) -> DhtReading:
        lg = self._lg
        try:
            lg.gpio_claim_output(self._handle, self._pin, 0)
            time.sleep(DHT22_START_LOW_S)
            self._edges = []
            # Zwolnienie linii (wejście z podciąganiem) rozpoczyma transmisję czujnika.
            lg.gpio_claim_alert(self._handle, self._pin, lg.FALLING_EDGE, lg.SET_PULL_UP)
            time.sleep(DHT22_TRANSMISSION_S)
            lg.gpio_claim_input(self._handle, self._pin, lg.SET_PULL_UP)
        except lg.error as e:
            raise DhtReadError(f"lgpio: {e}") from e
        return decode_dht22(list(self._edges))

    def close(self) -> None:
        self._callback.cancel()
        self._lg.gpio_free(self._handle, self._pin)
        self._lg.gpiochip_close(self._handle)


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
