import sys
import unittest
from unittest.mock import MagicMock, patch

# --- Hardware-Mocking ---
mock_sensor = MagicMock()
mock_motor = MagicMock()
lego_mock = MagicMock()
lego_mock.TouchSensor = mock_sensor
lego_mock.ColorSensor = mock_sensor
lego_mock.InfraredSensor = mock_sensor
sensor_mock = MagicMock()
sensor_mock.lego = lego_mock
sensor_mock.Sensor = mock_sensor

sys.modules["ev3dev2.motor"] = MagicMock(MoveTank=mock_motor)
sys.modules["ev3dev2.sensor.lego"] = lego_mock
sys.modules["ev3dev2.sensor"] = sensor_mock
sys.modules["ev3dev2"] = MagicMock()

class TestWaitForPhonePlaced(unittest.TestCase):
    @patch("robot.hardware.sleep")
    def test_waits_until_phone_placed(self, mock_sleep):
        from robot import hardware

        # Sensor ist erst nicht gedrückt, dann gedrückt
        pressed_states = [False, True]
        hardware.ev3_hardware.sensor_touch.is_pressed = property(lambda self: pressed_states.pop(0) if pressed_states else True)

        mock_ws = MagicMock()
        hardware.wait_for_phone_placed(mock_ws, timeout_seconds=1)

        # sleep sollte mindestens einmal aufgerufen werden
        self.assertTrue(mock_sleep.called)
        # Es sollte KEINE Fehlermeldung gesendet werden
        mock_ws.send.assert_not_called()

    @patch("robot.hardware.sleep")
    def test_sends_error_on_timeout(self, mock_sleep):
        from robot import hardware

        # Sensor bleibt immer ungedrückt
        hardware.ev3_hardware.sensor_touch.is_pressed = False

        mock_ws = MagicMock()
        # Wir lassen die Schleife einmal durchlaufen, dann Timeout
        call_count = {"count": 0}
        def sleep_side_effect(_):
            call_count["count"] += 1
            if call_count["count"] > 10:
                # Nach 10 sleeps, Sensor bleibt ungedrückt, Timeout wird ausgelöst
                raise KeyboardInterrupt()  # Bricht die Endlosschleife im Test ab
        mock_sleep.side_effect = sleep_side_effect

        with self.assertRaises(KeyboardInterrupt):
            hardware.wait_for_phone_placed(mock_ws, timeout_seconds=0.5)

        # Es sollte eine Fehlermeldung gesendet werden
        mock_ws.send.assert_called()

if __name__ == "__main__":
    unittest.main()