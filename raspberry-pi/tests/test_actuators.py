import unittest

from hub.actuators import SAFETY_HYSTERESIS_C, HeaterController, LedController, parse_command
from hub.config import HeaterSafetyConfig
from hub.hardware import MockRelay

SAFETY = HeaterSafetyConfig(command_timeout_s=30, max_temperature_c=35, max_invalid_readings=3)
MAX_READING_AGE_S = 40


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class ParseCommandTest(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(parse_command(b'{"state":"ON"}'))
        self.assertFalse(parse_command(b'{"state":"off"}'))

    def test_invalid(self):
        for payload in (b"ON", b"{}", b'{"state":1}', b'{"state":"MAYBE"}', b"[1]", b"\xff"):
            self.assertIsNone(parse_command(payload), payload)


class HeaterControllerTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.relay = MockRelay("heater")
        self.published: list[bool] = []
        self.heater = HeaterController(self.relay, SAFETY, MAX_READING_AGE_S, self.published.append, self.clock)
        self.heater.on_connection_change(True)
        self.heater.on_valid_reading(21.0)

    def test_on_and_off(self):
        self.heater.handle_command(True)
        self.assertTrue(self.relay.is_on)
        self.heater.handle_command(False)
        self.assertFalse(self.relay.is_on)
        self.assertEqual(self.published[-2:], [True, False])

    def test_blocked_without_any_reading(self):
        heater = HeaterController(MockRelay("h"), SAFETY, MAX_READING_AGE_S, lambda on: None, self.clock)
        heater.handle_command(True)
        self.assertFalse(heater.is_on)

    def test_heartbeat_timeout(self):
        self.heater.handle_command(True)
        self.clock.now += 20
        self.heater.handle_command(True)  # heartbeat odświeża termin
        self.clock.now += 25
        self.heater.on_valid_reading(21.0)
        self.heater.check_timeouts()
        self.assertTrue(self.relay.is_on)
        self.clock.now += 6
        self.heater.on_valid_reading(21.0)
        self.heater.check_timeouts()
        self.assertFalse(self.relay.is_on)
        self.assertFalse(self.published[-1])

    def test_disconnect_turns_off_and_clears_command(self):
        self.heater.handle_command(True)
        self.heater.on_connection_change(False)
        self.assertFalse(self.relay.is_on)
        self.heater.on_connection_change(True)
        self.assertFalse(self.relay.is_on)  # po reconnect potrzebna nowa komenda

    def test_over_temperature_with_hysteresis(self):
        self.heater.handle_command(True)
        self.heater.on_valid_reading(35.5)
        self.assertFalse(self.relay.is_on)
        self.heater.on_valid_reading(35.0 - SAFETY_HYSTERESIS_C / 2)
        self.assertFalse(self.relay.is_on)
        self.heater.on_valid_reading(35.0 - SAFETY_HYSTERESIS_C)
        self.assertTrue(self.relay.is_on)

    def test_invalid_readings(self):
        self.heater.handle_command(True)
        self.heater.on_invalid_reading()
        self.heater.on_invalid_reading()
        self.assertTrue(self.relay.is_on)
        self.heater.on_invalid_reading()
        self.assertFalse(self.relay.is_on)
        self.heater.on_valid_reading(21.0)
        self.assertTrue(self.relay.is_on)

    def test_stale_reading(self):
        self.heater.handle_command(True)
        self.clock.now += MAX_READING_AGE_S + 1
        self.heater.handle_command(True)
        self.assertFalse(self.relay.is_on)

    def test_shutdown(self):
        self.heater.handle_command(True)
        self.heater.shutdown()
        self.assertFalse(self.relay.is_on)
        self.assertFalse(self.published[-1])


class LedControllerTest(unittest.TestCase):
    def test_command_is_confirmed(self):
        relay = MockRelay("led")
        published: list[bool] = []
        led = LedController(relay, published.append)
        led.handle_command(True)
        led.handle_command(True)
        self.assertTrue(relay.is_on)
        self.assertEqual(published, [True, True])


if __name__ == "__main__":
    unittest.main()
