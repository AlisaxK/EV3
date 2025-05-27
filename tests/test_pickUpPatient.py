import unittest
from unittest.mock import MagicMock, patch
from robot.task import driveToRoom, pickupPatientFromWaitingRoom, turn_left_to_rooms


class TestPickupPatient(unittest.TestCase):
    @patch("main.robot.wait_for_phone_removed")
    @patch(
        "main.robot.follow_line_with_green_count",
        return_value=("TARGET_ROOM_REACHED", 1),
    )
    @patch("main.robot.sensor_ir")
    @patch("main.robot.sensor_right")
    @patch("main.robot.sensor_floor")
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
        mock_sensor_floor.color = 0  # BLACK
        mock_sensor_right.value.return_value = 3  # BLUE!
        mock_sensor_ir.proximity = 50  # kein Hindernis

        with patch("main.robot.turn_left_90_degrees"), patch(
            "main.robot.wait_for_phone_placed"
        ), patch("main.robot.tank_drive") as mock_drive:
            mock_drive.on_for_seconds.return_value = None
            mock_drive.on.return_value = None
            mock_drive.off.return_value = None

            pickupPatientFromWaitingRoom(mock_ws)

        mock_ws.send.assert_called_with(
            '{"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"}'
        )

    @patch("main.robot.wait_for_phone_placed")
    @patch("main.robot.tank_drive")
    @patch("main.robot.sensor_ir")
    @patch("main.robot.sensor_right")
    @patch("main.robot.sensor_floor")
    @patch(
        "main.robot.follow_line_with_green_count",
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
        mock_sensor_floor.color = 0  # BLACK
        mock_sensor_right.value.return_value = 3  # BLUE
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
