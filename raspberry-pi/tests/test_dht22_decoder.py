import unittest

from hub.hardware import DhtReadError, decode_dht22

ZERO_NS = 78_000
ONE_NS = 120_000
RESPONSE_NS = 160_000


def frame(humidity: float, temperature: float, corrupt_checksum: bool = False) -> list[int]:
    """Buduje znaczniki zboczy opadających tak, jak nadaje je czujnik."""
    h = round(humidity * 10)
    t = round(abs(temperature) * 10) | (0x8000 if temperature < 0 else 0)
    data = [h >> 8, h & 0xFF, t >> 8, t & 0xFF]
    data.append((sum(data) + (1 if corrupt_checksum else 0)) & 0xFF)
    bits = [int(b) for byte in data for b in f"{byte:08b}"]

    edges = [1_000_000]  # zbocze odpowiedzi czujnika
    edges.append(edges[-1] + RESPONSE_NS)  # początek bitu 0
    for bit in bits:
        edges.append(edges[-1] + (ONE_NS if bit else ZERO_NS))
    return edges


class DecodeDht22Test(unittest.TestCase):
    def test_positive(self):
        reading = decode_dht22(frame(45.3, 21.4))
        self.assertAlmostEqual(reading.humidity, 45.3)
        self.assertAlmostEqual(reading.temperature, 21.4)

    def test_negative_temperature(self):
        self.assertAlmostEqual(decode_dht22(frame(80.0, -5.2)).temperature, -5.2)

    def test_missed_response_edge(self):
        self.assertAlmostEqual(decode_dht22(frame(45.3, 21.4)[1:]).temperature, 21.4)

    def test_checksum(self):
        with self.assertRaises(DhtReadError):
            decode_dht22(frame(45.3, 21.4, corrupt_checksum=True))

    def test_too_few_edges(self):
        with self.assertRaises(DhtReadError):
            decode_dht22(frame(45.3, 21.4)[:30])


if __name__ == "__main__":
    unittest.main()
