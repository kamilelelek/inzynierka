import threading
import unittest

from hub.motion import MotionDetector

CLEAR_S = 0.2


class MotionDetectorTest(unittest.TestCase):
    def setUp(self):
        self.events: list[bool] = []
        self.cleared = threading.Event()

        def publish(motion: bool) -> None:
            self.events.append(motion)
            if not motion:
                self.cleared.set()

        self.detector = MotionDetector(CLEAR_S, publish)

    def tearDown(self):
        self.detector.close()

    def test_short_gaps_are_filtered(self):
        self.detector.on_input(True)
        self.detector.on_input(False)
        self.detector.on_input(True)  # zakłócenie w czasie krótszym niż CLEAR_S
        self.detector.on_input(False)
        self.assertTrue(self.cleared.wait(CLEAR_S * 5))
        self.assertEqual(self.events, [True, False])

    def test_no_clear_while_motion_continues(self):
        self.detector.on_input(True)
        self.assertFalse(self.cleared.wait(CLEAR_S * 2))
        self.assertEqual(self.events, [True])

    def test_low_without_motion_is_ignored(self):
        self.detector.on_input(False)
        self.assertFalse(self.cleared.wait(CLEAR_S * 2))
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
