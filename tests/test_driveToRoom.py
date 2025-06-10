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

class TestDriveToRoom(unittest.TestCase):
    @patch("robot.task._validate_room_list", return_value=True)
    @patch("robot.task.wait_for_phone_placed")
    @patch("robot.task.wait_for_phone_removed")
    @patch("robot.task._get_target_index", return_value=2)
    @patch("robot.task.turn_left_to_rooms")
    @patch("robot.task.follow_line_with_green_count", side_effect=[("TARGET_ROOM_REACHED", 1)])
    @patch("robot.task.turn_into_room")
    @patch("robot.task._handle_target_room_reached")
    @patch("robot.task.driveToBase")
    @patch("robot.task.follow_line_simple_to_room")
    def test_drive_to_room_deliver_patient(
        self,
        mock_follow_line_simple_to_room,
        mock_driveToBase,
        mock_handle_target_room_reached,
        mock_turn_into_room,
        mock_follow_line_with_green_count,
        mock_turn_left_to_rooms,
        mock_get_target_index,
        mock_wait_for_phone_removed,
        mock_wait_for_phone_placed,
        mock_validate_room_list,
    ):
        from robot import task

        task.positionRobot = task.POSITION_WAITING

        mock_ws = MagicMock()
        rooms = [0, 1, 0, 0]

        task.driveToRoom(rooms, ws=mock_ws, phone_removed=False, is_pickup=False)

        mock_wait_for_phone_placed.assert_called_once_with(mock_ws)
        mock_turn_left_to_rooms.assert_called_once_with(2, mock_ws)
        mock_handle_target_room_reached.assert_called_once_with(mock_ws, 2)
        mock_driveToBase.assert_called_once()
        mock_turn_into_room.assert_not_called()

if __name__ == "__main__":
    unittest.main()