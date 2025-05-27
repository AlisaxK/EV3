"""
import unittest
from unittest.mock import MagicMock, patch
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
from robot.task import driveToRoom, pickupPatientFromWaitingRoom, turn_left_to_rooms


class TestPickupPatient(unittest.TestCase):
    @patch("robot.hardware.wait_for_phone_removed")
    @patch(
        "robot.navigation.follow_line_with_green_count",
        return_value=("TARGET_ROOM_REACHED", 1),
    )
    @patch("robot.hardware.ev3_hardware.sensor_ir")
    @patch("robot.hardware.ev3_hardware.sensor_right")
    @patch("robot.hardware.ev3_hardware.sensor_floor")
    def test_pickup_patient_sends_correct_message(
        self,
        mock_sensor_floor,
        mock_sensor_right,
        mock_sensor_ir,
        mock_follow_line,
        mock_wait,
    ):

        mock_ws = MagicMock()

        # Sensorwerte simulieren
        mock_sensor_floor.color = 1  # BLACK
        mock_sensor_right.value.side_effect = lambda port=0: 3  # BLUE
        mock_sensor_ir.proximity = 50  # kein Hindernis

        with patch("robot.navigation.turn_left_90_degrees"), patch(
            "robot.hardware.wait_for_phone_placed"
        ), patch("robot.hardware.ev3_hardware.tank_drive") as mock_drive:
            mock_drive.on_for_seconds.return_value = None
            mock_drive.on.return_value = None
            mock_drive.off.return_value = None

            pickupPatientFromWaitingRoom(mock_ws)

        mock_ws.send.assert_called_with(
            '{"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"}'
        )

    @patch("robot.hardware.wait_for_phone_placed")
    @patch("robot.hardware.ev3_hardware.tank_drive")
    @patch("robot.hardware.ev3_hardware.sensor_ir")
    @patch("robot.hardware.ev3_hardware.sensor_right")
    @patch("robot.hardware.ev3_hardware.sensor_floor")
    @patch(
        "robot.navigation.follow_line_with_green_count",
        return_value=("TARGET_ROOM_REACHED", 1),
    )
    def test_turn_left_to_rooms_reaches_target(
        self,
        mock_follow_line,
        mock_sensor_floor,
        mock_sensor_right,
        mock_sensor_ir,
        mock_tank_drive,
        mock_wait_phone,
    ):
        mock_ws = MagicMock()

        # Sensorwerte vorbereiten, damit Schleifenbedingungen erfüllt werden
        mock_sensor_floor.color = 1  # BLACK
        mock_sensor_right.value.side_effect = lambda port=0: 3  # BLUE
        mock_sensor_ir.proximity = 50  # kein Hindernis

        # Simuliere Methoden des Antriebs
        mock_tank_drive.on.return_value = None
        mock_tank_drive.off.return_value = None
        mock_tank_drive.on_for_degrees.return_value = None

        # Jetzt rufen wir die Funktion auf
        turn_left_to_rooms(1, mock_ws)

        # Sicherstellen, dass Endzustand erreicht wurde
        mock_wait_phone.assert_called_once()
        mock_tank_drive.on_for_degrees.assert_any_call(
            left_speed=-20, right_speed=20, degrees=203
        )


if __name__ == "__main__":
    unittest.main()

"""
