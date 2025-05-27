import json
from robot.navigation import (
    follow_line_with_green_count,
    follow_line_simple,
    turn_into_room,
    turn_left_90_degrees,
    turn_right_90_degrees,
    turn_180_degrees,
    TARGET_ROOM_REACHED,
    POSITION_WAITING,
    POSITION_ROOM1,
    POSITION_ROOM2,
    POSITION_ROOM3,
    POSITION_START,
)
from robot.hardware import (
    ev3_hardware,
    ColorValues,
    wait_for_phone_placed,
    wait_for_phone_removed,
)

positionRobot = POSITION_START  # Initialize global position


def _handle_target_room_reached(ws, target_index):
    global positionRobot
    turn_into_room()
    wait_for_phone_placed(ws)
    if ws is not None:
        message = {"Type": "DRIVE_TO_ROOM_ANSWER", "Answer": "TRUE"}
        ws.send(json.dumps(message))
        print("DRIVE_TO_ROOM_ANSWER an Server gesendet.")

    print("positionRoboter", positionRobot)
    print("target_index", target_index)
    if target_index == 1:
        positionRobot = POSITION_WAITING
    elif target_index == 2:
        positionRobot = POSITION_ROOM1
    elif target_index == 3:
        positionRobot = POSITION_ROOM2
    elif target_index == 4:
        positionRobot = POSITION_ROOM3
    else:
        print("Unbekannter Zielraum Position nicht gesetzt.")

    print("Position Roboter gesetzt auf:", positionRobot)


def driveToRoom(rooms, ws=None):
    global positionRobot
    print("driveToRoom")
    print("positionRobot in driveToRoom", positionRobot)

    if (
        not isinstance(rooms, list)
        or len(rooms) != 4
        or not all(isinstance(x, int) and x in (0, 1) for x in rooms)
        or sum(rooms) == 0
    ):
        error_message = {
            "Type": "ERROR_INVALID_ROOM_FORMAT",
            "message": "Invalid rooms format: {rooms}",
        }
        print("Fehlerhafte Raumdaten empfangen:", rooms)
        if ws:
            ws.send(json.dumps(error_message))
            print("Fehlermeldung an Server gesendet: ERROR_INVALID_ROOM_FORMAT")
        return

    if rooms[0] == 1:
        wait_for_phone_placed(ws)
    else:
        wait_for_phone_removed(ws)

    target_index = None
    for i, val in enumerate(rooms):
        if val == 1:
            target_index = i + 1  # Zimmernummern starten bei 1
            break

    if target_index is None:
        print("Kein Zielraum angegeben Abbruch.")
        return

    green_count = 0

    print("Ziel: Zimmernummer {} - Roboter soll dort abbiegen.".format(target_index))
    from_waiting_room = positionRobot == POSITION_WAITING
    if from_waiting_room:
        print("Roboter kommt vom Warteraum und faehrt nach links")
        turn_left_to_rooms(target_index, ws)

    while True:
        result, green_count = follow_line_with_green_count(target_index, green_count)

        if result == TARGET_ROOM_REACHED:
            _handle_target_room_reached(ws, target_index)
            return

        else:  # Linienverfolgung im Raum
            follow_line_simple()


def turn_left_to_rooms(target_index, ws=None):
    print("Verlasse das Wartezimmer und fahre in den gewaehlten Raum:", target_index)
    # PHASE 1: Erste blaue Platte erkennen und links abbiegen
    while True:
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE:
            turn_left_90_degrees()
            return  # Wechsle zu Phase 2

        else:  # Linienverfolgung
            follow_line_simple()


def driveToBase(ws=None):
    """
    Roboter fährt zur Basis zurück:
    - Erkennt erste blaue Platte rechts → 90° rechts drehen
    - Fährt weiter bis zweite blaue Platte → 180° drehen und stoppen
    """
    print("Starte fahrt zur Basis")

    # PHASE 1: Erste blaue Platte erkennen und rechts abbiegen
    while True:
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE:
            turn_right_90_degrees()
            break  # Wechsle zu Phase 2

        else:  # Linienverfolgung
            follow_line_simple()

    # PHASE 2: Zweite blaue Platte erkennen und 180° drehen
    while True:
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE:
            turn_180_degrees()
            if ws is not None:
                message = {"Type": "DRIVE_TO_BASE_ANSWER", "Answer": "TRUE"}
                ws.send(json.dumps(message))
                print("DRIVE_TO_BASE_ANSWER an Server gesendet.")

            return

        else:  # Linienverfolgung
            follow_line_simple()

    global positionRobot
    positionRobot = POSITION_START
    print("Position zuruckgesetzt auf: ", positionRobot)


def pickupPatientFromWaitingRoom(ws=None):
    # Roboter fährt ins Wartezimmer um Patient abzuholen
    # Prüfen, ob Handy aufliegt, sonst error Code zurückgeben
    # success wenn erfolgreich
    print("Hole Patient im Wartezimmer ab")
    global positionRobot
    waitingRoom = [1, 0, 0, 0]
    driveToRoom(waitingRoom, ws)

    if ws is not None:
        message = {"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"}
        ws.send(json.dumps(message))
        print("PICK_PATIENT_ANSWER an Server gesendet.")

    positionRobot = POSITION_WAITING
    print("Position Roboter in pickupPatient gesetzt auf:", positionRobot)
