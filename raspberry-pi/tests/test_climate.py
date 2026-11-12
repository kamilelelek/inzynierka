import unittest

from hub.climate import SPIKE_CONFIRMATIONS, ClimateMonitor, ReadingFilter
from hub.hardware import DhtReadError, DhtReading


def r(t: float, h: float = 45.0) -> DhtReading:
    return DhtReading(t, h)


class ReadingFilterTest(unittest.TestCase):
    def test_out_of_range(self):
        f = ReadingFilter()
        self.assertIsNotNone(f.validate(r(-50)))
        self.assertIsNotNone(f.validate(r(21, 120)))
        self.assertIsNone(f.validate(r(21)))

    def test_single_spike_rejected(self):
        f = ReadingFilter()
        f.validate(r(21))
        self.assertIsNotNone(f.validate(r(60)))
        self.assertIsNone(f.validate(r(21.2)))

    def test_repeated_spike_accepted(self):
        f = ReadingFilter()
        f.validate(r(21))
        results = [f.validate(r(30)) for _ in range(SPIKE_CONFIRMATIONS)]
        self.assertIsNone(results[-1])
        self.assertEqual(f.smoothed().temperature, 30)

    def test_median(self):
        f = ReadingFilter()
        for t in (21.0, 23.0, 22.0):
            f.validate(r(t))
        self.assertEqual(f.smoothed().temperature, 22.0)


class FakeSensor:
    def __init__(self, results):
        self.results = list(results)

    def read(self):
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def close(self):
        pass


class ClimateMonitorTest(unittest.TestCase):
    def test_callbacks(self):
        published, valid, invalid = [], [], []
        sensor = FakeSensor([r(21), DhtReadError("x"), r(80.5)])
        monitor = ClimateMonitor(sensor, 10, published.append, valid.append, lambda: invalid.append(1))
        for _ in range(3):
            monitor.read_once()
        self.assertEqual(valid, [r(21)])
        self.assertEqual(published, [r(21)])
        self.assertEqual(len(invalid), 2)


if __name__ == "__main__":
    unittest.main()
