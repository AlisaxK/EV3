import json
from robot.navigation import (
    follow_line_with_green_count,
    follow_line_simple_to_room,
    follow_line_simple_to_base,
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

positionRobot = POSITION_START


def _handle_target_room_reached(ws, target_index):
    global positionRobot
    turn_into_room()
    if ws is not None:
        message = {"Type": "DRIVE_TO_ROOM_ANSWER", "Answer": "TRUE"}
        ws.send(json.dumps(message))

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


def driveToRoom(rooms, ws=None, phone_removed=True, is_pickup=False):
    global positionRobot

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
        if ws:
            ws.send(json.dumps(error_message))
        return
        
    if bool(phone_removed):
        wait_for_phone_removed(ws)
    else:
        wait_for_phone_placed(ws)

    target_index = None
    for i, val in enumerate(rooms):
        if val == 1:
            target_index = i + 1
            break

    if target_index is None:
        return

    green_count = 0

    from_waiting_room = positionRobot == POSITION_WAITING
    if from_waiting_room:
        turn_left_to_rooms(target_index, ws)
        green_count = 1

    while True:
        result, green_count = follow_line_with_green_count(target_index, green_count)

        if result == TARGET_ROOM_REACHED:
            if is_pickup:
                turn_into_room()
                return
            else:
                _handle_target_room_reached(ws, target_index)
                driveToBase(ws)
                return

        else:
            follow_line_simple_to_room()


def turn_left_to_rooms(target_index, ws=None):
    while True:
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE:
            turn_left_90_degrees()
            return

        else:
            follow_line_simple_to_base()


def driveToBase(ws=None):
    
    wait_for_phone_placed(ws)

    while True:
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE:
            turn_right_90_degrees()
            break

        else:
            follow_line_simple_to_base()

    while True:
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE:
            turn_180_degrees()
            if ws is not None:
                message = {"Type": "DRIVE_TO_BASE_ANSWER", "Answer": "TRUE"}
                ws.send(json.dumps(message))
                print("DRIVE_TO_BASE_ANSWER an Server gesendet.")

            global positionRobot
            positionRobot = POSITION_START
            print("Position zuruckgesetzt auf: ", positionRobot)
            return

        else:
            follow_line_simple_to_base()


def pickupPatientFromWaitingRoom(ws=None):
    print("Hole Patient im Wartezimmer ab")
    global positionRobot
    waitingRoom = [1, 0, 0, 0]
    driveToRoom(waitingRoom, ws, phone_removed=False, is_pickup=True)

    if ws is not None:
        message = {"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"}
        ws.send(json.dumps(message))

    positionRobot = POSITION_WAITING