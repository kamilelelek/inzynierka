"""Symulator huba do testów backendu bez Raspberry Pi i bez czujników.

Publikuje na tych samych topikach i w tym samym formacie co hub:
- status online/offline (retain, LWT),
- odczyty klimatu co --interval s (temperatura rośnie, gdy grzałka jest ON, i opada do --ambient),
- zdarzenia ruchu co --motion-every s (ruch, a po --motion-clear s koniec ruchu),
- stan LED i grzałki w odpowiedzi na komendy led/set i heater/set (grzałka OFF po 30 s bez komendy).

Nie uruchamiaj go równocześnie z prawdziwym hubem o tym samym HUB_ID.

Przykłady (z katalogu raspberry-pi):
    ..\\.venv\\Scripts\\python tools\\fake_sensors.py --host kamil.local
    ..\\.venv\\Scripts\\python tools\\fake_sensors.py --interval 2 --motion-every 15 --count 20
    ..\\.venv\\Scripts\\python tools\\fake_sensors.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("fake_sensors")

HEATER_TIMEOUT_S = 30


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_env() -> None:
    """Wczytuje raspberry-pi/.env (jeśli jest python-dotenv), żeby domyślnie użyć tego samego brokera co hub."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def parse_args() -> argparse.Namespace:
    load_env()
    p = argparse.ArgumentParser(description="Symulator danych z czujników huba (MQTT)")
    p.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    p.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    p.add_argument("--username", default=os.getenv("MQTT_USERNAME") or None)
    p.add_argument("--password", default=os.getenv("MQTT_PASSWORD") or None)
    p.add_argument("--hub-id", default=os.getenv("HUB_ID", "hub1"))
    p.add_argument("--interval", type=float, default=5.0, help="co ile s odczyt klimatu")
    p.add_argument("--ambient", type=float, default=20.0, help="temperatura otoczenia [°C]")
    p.add_argument("--temp", type=float, default=None, help="temperatura startowa (domyślnie = ambient)")
    p.add_argument("--humidity", type=float, default=45.0, help="wilgotność startowa [%%]")
    p.add_argument("--heat-rate", type=float, default=0.3, help="przyrost temp. na cykl przy grzałce ON")
    p.add_argument("--motion-every", type=float, default=30.0, help="co ile s ruch (0 = wyłączone)")
    p.add_argument("--motion-clear", type=float, default=5.0, help="po ilu s koniec ruchu")
    p.add_argument("--count", type=int, default=0, help="liczba odczytów klimatu (0 = bez końca)")
    p.add_argument("--dry-run", action="store_true", help="tylko wypisuj wiadomości, bez brokera")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


class Publisher:
    """Wysyła JSON przez paho albo (dry-run) wypisuje go na ekran."""

    def __init__(self, args: argparse.Namespace, base: str) -> None:
        self.base = base
        self.client = None
        if args.dry_run:
            return
        import paho.mqtt.client as mqtt
        from paho.mqtt.enums import CallbackAPIVersion

        self.client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=f"{args.hub_id}-fake-{os.getpid()}")
        if args.username:
            self.client.username_pw_set(args.username, args.password)
        self.client.will_set(f"{base}/status", json.dumps({"state": "offline"}), qos=1, retain=True)

    def publish(self, suffix: str, payload: dict, qos: int, retain: bool = False) -> None:
        topic = f"{self.base}/{suffix}"
        text = json.dumps(payload)
        log.info("-> %s %s", topic, text)
        if self.client is not None:
            self.client.publish(topic, text, qos=qos, retain=retain)


class FakeHub:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.pub = Publisher(args, f"home/{args.hub_id}")
        self.lock = threading.Lock()
        self.temperature = args.ambient if args.temp is None else args.temp
        self.humidity = args.humidity
        self.led_on = False
        self.heater_on = False
        self.heater_last_cmd = 0.0

    # --- komendy z backendu ---
    def on_message(self, client, userdata, message) -> None:
        device = message.topic.split("/")[-2]
        try:
            state = json.loads(message.payload)["state"]
            on = {"ON": True, "OFF": False}[state]
        except (ValueError, KeyError, TypeError):
            log.warning("Zła komenda na %s: %r", message.topic, message.payload)
            return
        log.info("<- %s %s", message.topic, message.payload.decode(errors="replace"))
        with self.lock:
            if device == "led":
                self.led_on = on
            else:
                self.heater_on = on
                self.heater_last_cmd = time.monotonic()
        self.publish_state(device, on)

    def on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code.is_failure:
            log.error("Broker odrzucił połączenie: %s", reason_code)
            return
        log.info("Połączono z %s:%d", self.args.host, self.args.port)
        client.subscribe(f"{self.pub.base}/led/set", qos=1)
        client.subscribe(f"{self.pub.base}/heater/set", qos=1)
        self.pub.publish("status", {"state": "online", "ts": utc_now_iso()}, qos=1, retain=True)
        self.publish_state("led", self.led_on)
        self.publish_state("heater", self.heater_on)

    def publish_state(self, device: str, on: bool) -> None:
        self.pub.publish(f"{device}/state", {"state": "ON" if on else "OFF", "ts": utc_now_iso()}, qos=1, retain=True)

    # --- symulacja ---
    def step_climate(self) -> None:
        with self.lock:
            if self.heater_on and time.monotonic() - self.heater_last_cmd > HEATER_TIMEOUT_S:
                log.warning("Brak komendy heater/set przez %d s, grzałka OFF (jak fail-safe na Pi)", HEATER_TIMEOUT_S)
                self.heater_on = False
                heater_timed_out = True
            else:
                heater_timed_out = False
            if self.heater_on:
                self.temperature += self.args.heat_rate
            else:
                self.temperature += (self.args.ambient - self.temperature) * 0.05
            self.temperature += random.uniform(-0.1, 0.1)
            self.humidity = min(95.0, max(20.0, self.humidity + random.uniform(-0.5, 0.5)))
            payload = {
                "temperature": round(self.temperature, 1),
                "humidity": round(self.humidity, 1),
                "ts": utc_now_iso(),
            }
        if heater_timed_out:
            self.publish_state("heater", False)
        self.pub.publish("climate/telemetry", payload, qos=0)

    def publish_motion(self, detected: bool) -> None:
        self.pub.publish("motion/event", {"motion": detected, "ts": utc_now_iso()}, qos=1)

    def run(self) -> None:
        client = self.pub.client
        if client is not None:
            client.on_connect = self.on_connect
            client.message_callback_add(f"{self.pub.base}/+/set", self.on_message)
            client.connect_async(self.args.host, self.args.port, keepalive=30)
            client.loop_start()

        now = time.monotonic()
        next_climate = now
        next_motion = now + self.args.motion_every if self.args.motion_every > 0 else None
        motion_clear_at = None
        sent = 0
        try:
            while self.args.count == 0 or sent < self.args.count:
                now = time.monotonic()
                connected = client is None or client.is_connected()
                if now >= next_climate:
                    next_climate += self.args.interval
                    if connected:
                        self.step_climate()
                        sent += 1
                    else:
                        log.info("Czekam na połączenie z %s:%d", self.args.host, self.args.port)
                if connected and next_motion is not None and now >= next_motion:
                    next_motion += self.args.motion_every
                    self.publish_motion(True)
                    motion_clear_at = now + self.args.motion_clear
                if connected and motion_clear_at is not None and now >= motion_clear_at:
                    self.publish_motion(False)
                    motion_clear_at = None
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            if client is not None and client.is_connected():
                info = client.publish(f"{self.pub.base}/status", json.dumps({"state": "offline"}), qos=1, retain=True)
                info.wait_for_publish(timeout=2)
                client.disconnect()
            if client is not None:
                client.loop_stop()
            log.info("Koniec, wysłano %d odczytów klimatu", sent)


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    FakeHub(args).run()


if __name__ == "__main__":
    main()
