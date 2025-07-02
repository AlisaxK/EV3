import sys
import unittest
from unittest.mock import MagicMock, patch

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

class TestDriveToBase(unittest.TestCase):
    @patch("robot.task.turn_180_degrees")
    @patch("robot.task.turn_right_90_degrees")
    @patch("robot.task.follow_line_simple_to_base")
    @patch("robot.task.wait_for_phone_placed")
    def test_drive_to_base_sends_message_and_resets_position(
        self,
        mock_wait_for_phone_placed,
        mock_follow_line_simple_to_base,
        mock_turn_right_90_degrees,
        mock_turn_180_degrees,
    ):
        from robot import task

        task.ev3_hardware.sensor_right.value = MagicMock(side_effect=[task.ColorValues.BLUE, task.ColorValues.BLUE])

        mock_ws = MagicMock()
        task.positionRobot = "irgendein_wert"

        task.driveToBase(mock_ws)

        mock_wait_for_phone_placed.assert_called_once_with(mock_ws)
        mock_turn_right_90_degrees.assert_called_once()
        mock_turn_180_degrees.assert_called_once()
        mock_ws.send.assert_called_once_with('{"Type": "DRIVE_TO_BASE_ANSWER", "Answer": "TRUE"}')
        self.assertEqual(task.positionRobot, task.POSITION_START)

if __name__ == "__main__":
    unittest.main()