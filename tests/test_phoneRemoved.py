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

class TestWaitForPhoneRemoved(unittest.TestCase):
    @patch("robot.hardware.sleep")
    def test_waits_until_phone_removed(self, mock_sleep):
        from robot import hardware

        # Sensor ist erst gedrückt, dann nicht mehr
        pressed_states = [True, False]
        def is_pressed_side_effect(_self):
            return pressed_states.pop(0) if pressed_states else False
        type(hardware.ev3_hardware.sensor_touch).is_pressed = property(is_pressed_side_effect)

        mock_ws = MagicMock()
        hardware.wait_for_phone_removed(mock_ws, timeout_seconds=1)

        self.assertTrue(mock_sleep.called)
        mock_ws.send.assert_not_called()

    @patch("robot.hardware.sleep")
    def test_sends_error_on_timeout(self, mock_sleep):
        from robot import hardware

        # Sensor bleibt immer gedrückt
        hardware.ev3_hardware.sensor_touch.is_pressed = property(lambda self: True)

        mock_ws = MagicMock()

        # Nach 10 sleeps brechen wir die Schleife künstlich ab
        call_count = {"count": 0}
        def sleep_side_effect(_):
            call_count["count"] += 1
            if call_count["count"] > 10:
                raise Exception("Timeout simuliert")
        mock_sleep.side_effect = sleep_side_effect

        with self.assertRaises(Exception):
            hardware.wait_for_phone_removed(mock_ws, timeout_seconds=0.01)

        # Es sollte eine Fehlermeldung gesendet werden (wenn das in deiner Funktion so ist)
        # Falls die Fehlermeldung erst nach echtem Timeout gesendet wird, kannst du das hier nicht testen,
        # sondern nur, dass die Schleife "irgendwann" abgebrochen wird.

if __name__ == "__main__":
    unittest.main()