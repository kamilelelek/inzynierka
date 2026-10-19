"""Konfiguracja huba wczytywana ze zmiennych środowiskowych (plik .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# DHT22 nie pozwala na odczyt częściej niż co ~2 s.
DHT22_MIN_INTERVAL_S = 2.0


class ConfigError(ValueError):
    """Brakująca lub niepoprawna wartość konfiguracji."""


def _get_str(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        raise ConfigError(f"Brak wymaganej zmiennej {name}")
    return value.strip()


def _get_optional_str(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


def _get_int(name: str, default: int | None = None) -> int:
    raw = _get_str(name, None if default is None else str(default))
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"{name} musi być liczbą całkowitą, jest: {raw!r}") from None


def _get_float(name: str, default: float | None = None) -> float:
    raw = _get_str(name, None if default is None else str(default))
    try:
        return float(raw)
    except ValueError:
        raise ConfigError(f"{name} musi być liczbą, jest: {raw!r}") from None


def _get_bool(name: str, default: bool | None = None) -> bool:
    raw = _get_str(name, None if default is None else str(default)).lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    raise ConfigError(f"{name} musi być true/false, jest: {raw!r}")


def _get_bcm_pin(name: str) -> int:
    pin = _get_int(name)
    if not 0 <= pin <= 27:
        raise ConfigError(f"{name} musi być numerem BCM 0-27, jest: {pin}")
    return pin


@dataclass(frozen=True)
class MqttConfig:
    host: str
    port: int
    client_id: str
    username: str | None
    password: str | None
    keepalive_s: int
    reconnect_min_delay_s: int
    reconnect_max_delay_s: int


@dataclass(frozen=True)
class GpioConfig:
    mock: bool
    dht_pin: int
    pir_pin: int
    led_relay_pin: int
    heater_relay_pin: int


@dataclass(frozen=True)
class HeaterSafetyConfig:
    command_timeout_s: float
    max_temperature_c: float
    max_invalid_readings: int


@dataclass(frozen=True)
class Config:
    hub_id: str
    log_level: str
    dht_interval_s: float
    mqtt: MqttConfig
    gpio: GpioConfig
    heater: HeaterSafetyConfig


def load_config(env_file: Path = DEFAULT_ENV_FILE) -> Config:
    """Wczytuje .env (zmienne już ustawione w środowisku mają pierwszeństwo) i waliduje wartości."""
    load_dotenv(env_file, override=False)

    hub_id = _get_str("HUB_ID")

    mqtt = MqttConfig(
        host=_get_str("MQTT_HOST"),
        port=_get_int("MQTT_PORT"),
        client_id=_get_str("MQTT_CLIENT_ID", f"{hub_id}-pi"),
        username=_get_optional_str("MQTT_USERNAME"),
        password=_get_optional_str("MQTT_PASSWORD"),
        keepalive_s=_get_int("MQTT_KEEPALIVE_S", 30),
        reconnect_min_delay_s=_get_int("MQTT_RECONNECT_MIN_DELAY_S", 1),
        reconnect_max_delay_s=_get_int("MQTT_RECONNECT_MAX_DELAY_S", 30),
    )
    if not 1 <= mqtt.port <= 65535:
        raise ConfigError(f"MQTT_PORT poza zakresem: {mqtt.port}")
    if not 0 < mqtt.reconnect_min_delay_s <= mqtt.reconnect_max_delay_s:
        raise ConfigError("Wymagane 0 < MQTT_RECONNECT_MIN_DELAY_S <= MQTT_RECONNECT_MAX_DELAY_S")

    gpio = GpioConfig(
        mock=_get_bool("GPIO_MOCK", False),
        dht_pin=_get_bcm_pin("GPIO_DHT22"),
        pir_pin=_get_bcm_pin("GPIO_PIR"),
        led_relay_pin=_get_bcm_pin("GPIO_RELAY_LED"),
        heater_relay_pin=_get_bcm_pin("GPIO_RELAY_HEATER"),
    )
    pins = [gpio.dht_pin, gpio.pir_pin, gpio.led_relay_pin, gpio.heater_relay_pin]
    if len(set(pins)) != len(pins):
        raise ConfigError(f"Piny GPIO muszą być różne: {pins}")

    dht_interval_s = _get_float("DHT22_INTERVAL_S")
    if dht_interval_s < DHT22_MIN_INTERVAL_S:
        raise ConfigError(f"DHT22_INTERVAL_S musi wynosić co najmniej {DHT22_MIN_INTERVAL_S} s")

    heater = HeaterSafetyConfig(
        command_timeout_s=_get_float("HEATER_COMMAND_TIMEOUT_S"),
        max_temperature_c=_get_float("HEATER_MAX_TEMPERATURE_C"),
        max_invalid_readings=_get_int("HEATER_MAX_INVALID_READINGS"),
    )
    if heater.command_timeout_s <= 0 or heater.max_invalid_readings < 1:
        raise ConfigError("HEATER_COMMAND_TIMEOUT_S > 0 oraz HEATER_MAX_INVALID_READINGS >= 1")

    return Config(
        hub_id=hub_id,
        log_level=_get_str("LOG_LEVEL", "INFO").upper(),
        dht_interval_s=dht_interval_s,
        mqtt=mqtt,
        gpio=gpio,
        heater=heater,
    )
