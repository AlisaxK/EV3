import unittest
from unittest.mock import Mock, patch, call, ANY, MagicMock
import sys

mock_sensor = MagicMock()
mock_motor = MagicMock()

# mock ev3dev2.sensor.lego
lego_mock = MagicMock()
lego_mock.TouchSensor = mock_sensor
lego_mock.ColorSensor = mock_sensor
lego_mock.InfraredSensor = mock_sensor

# mock v3dev2.sensor m
sensor_mock = MagicMock()
sensor_mock.lego = lego_mock
sensor_mock.Sensor = mock_sensor

sys.modules["ev3dev2.motor"] = MagicMock(MoveTank=mock_motor)
sys.modules["ev3dev2.sensor.lego"] = lego_mock
sys.modules["ev3dev2.sensor"] = sensor_mock
sys.modules["ev3dev2"] = MagicMock()


from main import EV3CommandHandler


class TestEV3CommandHandler(unittest.TestCase):
    def setUp(self):
        self.mock_ws = MagicMock()
        self.handler = EV3CommandHandler(ws=self.mock_ws)

    @patch("main.driveToRoom")
    def test_handle_drive_to_room_string(self, mock_drive):
        json_string = "[0, 1, 0, 0]"
        command = {"Type": "DRIVE_TO_ROOM", "Target": json_string}
        self.handler.handle_command(command)

        mock_drive.assert_called_once_with([0, 1, 0, 0], self.mock_ws)

    @patch("main.driveToRoom")
    def test_handle_drive_to_room_array(self, mock_drive):
        command = {"Type": "DRIVE_TO_ROOM", "Target": [0, 0, 1, 0]}
        self.handler.handle_command(command)

        mock_drive.assert_called_once_with([0, 0, 1, 0], self.mock_ws)

    @patch("main.driveToBase")
    def test_handle_drive_to_base(self, mock_drive):
        command = {"Type": "DRIVE_TO_BASE"}
        self.handler.handle_command(command)

        mock_drive.assert_called_once_with(self.mock_ws)

    @patch("main.pickupPatientFromWaitingRoom")
    def test_handle_pick_patient(self, mock_pickup):
        command = {"Type": "PICK_PATIENT"}
        self.handler.handle_command(command)

        mock_pickup.assert_called_once_with(self.mock_ws)

    def test_handle_unknown_command(self):
        command = {"Type": "DOES_NOT_EXIST"}
        self.handler.handle_command(command)

        self.mock_ws.send.assert_called_with(
            '{"Type": "error", "Answer": "unknown_command"}'
        )

    def test_handle_command_while_busy(self):
        self.handler.busy = True
        command = {"Type": "DRIVE_TO_BASE"}
        self.handler.handle_command(command)

        self.mock_ws.send.assert_called_with(
            '{"Type": "status", "message": "busy", "rejected_command": "DRIVE_TO_BASE"}'
        )

    def test_handle_command_with_exception(self):
        self.handler.busy = False

        # command that triggers exception
        with patch("main.driveToRoom", side_effect=Exception("Exception!")):
            command = {"Type": "DRIVE_TO_ROOM", "Target": [1, 0, 0, 0]}
            self.handler.handle_command(command)

        self.mock_ws.send.assert_called_with(
            '{"Type": "error", "Answer": "Exception!"}'
        )

    @patch("main.driveToRoom")
    def test_handle_drive_to_room_with_invalid_json_string(self, mock_drive):
        invalid_json = "not a list"
        command = {"Type": "DRIVE_TO_ROOM", "Target": invalid_json}
        self.handler.handle_command(command)

        mock_drive.assert_called_once_with([], self.mock_ws)
