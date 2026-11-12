# Hub Raspberry Pi

Skrypt publikuje odczyty DHT22 i zdarzenia PIR przez MQTT oraz steruje przekaźnikami LED i grzałki.
Topiki i payloady opisuje tabela w CLAUDE.md; konfiguracja jest w `.env` (wzór: `.env.example`).

## Moduły (`hub/`)

| Plik | Rola |
|---|---|
| `config.py` | wczytanie i walidacja `.env` |
| `mqtt_client.py` | połączenie z brokerem, LWT, status online/offline, subskrypcje |
| `hardware.py` | przekaźniki, DHT22, PIR: prawdziwe GPIO albo symulacja (`GPIO_MOCK=true`) |
| `climate.py` | cykliczny odczyt DHT22, odrzucanie błędów i skoków, mediana z 3 odczytów |
| `motion.py` | debounce PIR (koniec ruchu po `MOTION_CLEAR_S` bez sygnału) |
| `actuators.py` | LED, grzałka z zabezpieczeniami (heartbeat, rozłączenie, próg temperatury, błędy czujnika) |

## Uruchomienie na PC (tryb mock)

```powershell
cd raspberry-pi
copy .env.example .env      # GPIO_MOCK=true, MQTT_HOST = adres brokera
..\.venv\Scripts\python -m hub
..\.venv\Scripts\python -m unittest discover -s tests -t .
```

## Wdrożenie na Raspberry Pi

```bash
sudo apt update
sudo apt install -y git mosquitto mosquitto-clients python3-venv python3-lgpio
git clone https://github.com/kamilelelek/inzynierka.git ~/inzynierka
cd ~/inzynierka/raspberry-pi
# --system-site-packages: gpiozero i odczyt DHT22 korzystają z systemowego lgpio (z pip trzeba by je kompilować)
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env   # GPIO_MOCK=false, MQTT_HOST=localhost
.venv/bin/python -m hub
```

Aktualizacja: `cd ~/inzynierka && git pull`, potem restart skryptu lub usługi.

### Test bez backendu (drugi terminal SSH)

```bash
mosquitto_sub -h localhost -t 'home/hub1/#' -v
mosquitto_pub -h localhost -t home/hub1/led/set -m '{"state":"ON"}'
mosquitto_pub -h localhost -t home/hub1/heater/set -m '{"state":"ON"}'   # bez powtórzeń OFF po HEATER_COMMAND_TIMEOUT_S
```

## Autostart (systemd)

```bash
sudo cp deploy/smarthome-hub.service /etc/systemd/system/   # wcześniej popraw User i ścieżki
sudo systemctl daemon-reload
sudo systemctl enable --now smarthome-hub
journalctl -u smarthome-hub -f
```

`ExecStopPost` ustawia piny przekaźników w stan wysoki (OFF) także po crashu skryptu.
