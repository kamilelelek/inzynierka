"""Połączenie z brokerem MQTT: LWT, status online/offline, automatyczny reconnect."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from hub.config import MqttConfig

log = logging.getLogger(__name__)

QOS_TELEMETRY = 0
QOS_RELIABLE = 1


def utc_now_iso() -> str:
    """Znacznik czasu ISO 8601 UTC, np. 2026-10-19T12:00:00Z."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class Topics:
    status: str
    climate_telemetry: str
    motion_event: str
    led_set: str
    led_state: str
    heater_set: str
    heater_state: str

    @classmethod
    def for_hub(cls, hub_id: str) -> Topics:
        base = f"home/{hub_id}"
        return cls(
            status=f"{base}/status",
            climate_telemetry=f"{base}/climate/telemetry",
            motion_event=f"{base}/motion/event",
            led_set=f"{base}/led/set",
            led_state=f"{base}/led/state",
            heater_set=f"{base}/heater/set",
            heater_state=f"{base}/heater/state",
        )


class HubMqttClient:
    """Opakowanie klienta paho: pętla sieciowa w osobnym wątku, reconnect obsługuje paho."""

    def __init__(self, config: MqttConfig, topics: Topics) -> None:
        self._config = config
        self._topics = topics

        self._client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=config.client_id)
        if config.username:
            self._client.username_pw_set(config.username, config.password)

        # LWT: broker opublikuje to, jeśli hub zniknie bez poprawnego rozłączenia.
        self._client.will_set(
            topics.status, json.dumps({"state": "offline"}), qos=QOS_RELIABLE, retain=True
        )
        self._client.reconnect_delay_set(
            min_delay=config.reconnect_min_delay_s, max_delay=config.reconnect_max_delay_s
        )
        self._subscriptions: dict[str, Callable[[bytes], None]] = {}
        self._connection_listeners: list[Callable[[bool], None]] = []

        self._client.on_connect = self._on_connect
        self._client.on_connect_fail = self._on_connect_fail
        self._client.on_disconnect = self._on_disconnect

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected()

    def subscribe(self, topic: str, handler: Callable[[bytes], None]) -> None:
        """Rejestruje obsługę komend; subskrypcja jest odnawiana po każdym (re)connect."""
        self._subscriptions[topic] = handler

        def on_message(client, userdata, message: mqtt.MQTTMessage) -> None:
            log.debug("<- %s %r", message.topic, message.payload)
            try:
                handler(message.payload)
            except Exception:
                # Wyjątek w callbacku zatrzymałby wątek sieciowy paho.
                log.exception("Błąd obsługi wiadomości z %s", message.topic)

        self._client.message_callback_add(topic, on_message)
        if self.is_connected:
            self._client.subscribe(topic, qos=QOS_RELIABLE)

    def add_connection_listener(self, listener: Callable[[bool], None]) -> None:
        """listener(True) po połączeniu (po subskrypcjach i statusie online), listener(False) po utracie."""
        self._connection_listeners.append(listener)

    def start(self) -> None:
        log.info("Łączenie z brokerem %s:%d", self._config.host, self._config.port)
        # connect_async + loop_start: paho ponawia także pierwsze, nieudane połączenie.
        self._client.connect_async(self._config.host, self._config.port, self._config.keepalive_s)
        self._client.loop_start()

    def stop(self) -> None:
        # Przy poprawnym rozłączeniu broker NIE wysyła LWT, więc status offline publikujemy sami.
        if self.is_connected:
            info = self.publish_json(self._topics.status, {"state": "offline"}, QOS_RELIABLE, retain=True)
            try:
                if info is not None:
                    info.wait_for_publish(timeout=2)
            except (RuntimeError, ValueError):
                log.warning("Nie udało się wysłać statusu offline")
        self._client.disconnect()
        self._client.loop_stop()
        log.info("Klient MQTT zatrzymany")

    def publish_json(
        self, topic: str, payload: dict[str, Any], qos: int, retain: bool = False
    ) -> mqtt.MQTTMessageInfo | None:
        if not self.is_connected:
            # Stan urządzeń jest odświeżany po reconnect, a telemetria i tak przyjdzie w kolejnym cyklu.
            log.debug("Brak połączenia, pomijam %s %s", topic, payload)
            return None
        info = self._client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning("Publikacja na %s nieudana: %s", topic, mqtt.error_string(info.rc))
        else:
            log.debug("-> %s %s", topic, payload)
        return info

    def publish_device_state(self, topic: str, on: bool) -> None:
        self.publish_json(topic, {"state": "ON" if on else "OFF", "ts": utc_now_iso()}, QOS_RELIABLE, retain=True)

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code.is_failure:
            log.error("Broker odrzucił połączenie: %s", reason_code)
            return
        log.info("Połączono z brokerem")
        for topic in self._subscriptions:
            client.subscribe(topic, qos=QOS_RELIABLE)
        self.publish_json(
            self._topics.status, {"state": "online", "ts": utc_now_iso()}, QOS_RELIABLE, retain=True
        )
        self._notify_listeners(True)

    def _on_connect_fail(self, client, userdata) -> None:
        log.warning("Broker %s:%d nieosiągalny, ponawiam", self._config.host, self._config.port)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code.is_failure:
            log.warning("Utracono połączenie z brokerem (%s), ponawiam", reason_code)
        else:
            log.info("Rozłączono z brokerem")
        self._notify_listeners(False)

    def _notify_listeners(self, connected: bool) -> None:
        for listener in self._connection_listeners:
            try:
                listener(connected)
            except Exception:
                log.exception("Błąd w obsłudze zmiany połączenia")
