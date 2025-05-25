from robot.navigation import *
#import robot.hardware as hardware


def wait_for_phone_removed(ws=None, timeout_seconds=5):
    print("Warte darauf, dass das Handy entfernt wird...")
    waited = 0
    while sensor_touch.is_pressed:
        sleep(0.1)
        waited += 0.1

        if waited >= timeout_seconds:
            # print("Fehler: Handy wurde nach 5 Sekunden noch nicht entfernt!")
            if ws is not None:
                message = {"message": "ERROR_PHONE_NOT_REMOVED"}
                ws.send(json.dumps(message))
                print("Fehler-Nachricht an Server gesendet: ERROR_PHONE_NOT_REMOVED")
            waited = 0
    print("Handy entfernt. Starte Raumwahl.")
    sleep(5)

def wait_for_phone_placed(ws=None, timeout_seconds=5):
    # print("Warte darauf, dass das Handy wieder platziert wird...")
    waited = 0

    while not sensor_touch.is_pressed:
        sleep(0.1)
        waited += 0.1

        if waited >= timeout_seconds:
            print("Fehler: Handy noch nicht erkannt nach 5 Sekunden!")
            if ws is not None:
                message = {"message": "ERROR_NO_PHONE_DETECTED"}
                ws.send(json.dumps(message))
                print("Fehler-Nachricht an Server gesendet: ERROR_NO_PHONE_DETECTED")
            waited = 0  # **Reset**:
    print("Handy erkannt. Roboter faehrt weiter.")
    sleep(5)


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
        floor_color = sensor_floor.color
        result, green_count = follow_line_with_green_count(target_index, green_count, floor_color)

        if result == TARGET_ROOM_REACHED:
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
            return

        else:  # Linienverfolgung im Raum
            follow_line_simple(floor_color)

def turn_left_to_rooms(target_index, ws=None): 
    print("Verlasse das Wartezimmer und fahre in den gewaehlten Raum:", target_index)
    # PHASE 1: Erste blaue Platte erkennen und links abbiegen
    while True:
        floor_color = sensor_floor.color
        right_color_id = sensor_right.value(0)

        if right_color_id == BLUE:
            turn_left_90_degrees()
            return  # Wechsle zu Phase 2

        else:  # Linienverfolgung
            follow_line_simple(floor_color)
                    

def driveToBase(ws=None):
    """
    Roboter fährt zur Basis zurück:
    - Erkennt erste blaue Platte rechts → 90° rechts drehen
    - Fährt weiter bis zweite blaue Platte → 180° drehen und stoppen
    """
    print("Starte fahrt zur Basis")

    # PHASE 1: Erste blaue Platte erkennen und rechts abbiegen
    while True:
        floor_color = sensor_floor.color
        right_color_id = sensor_right.value(0)


        if right_color_id == BLUE:
            turn_right_90_degrees()
            break  # Wechsle zu Phase 2

        else:  # Linienverfolgung
            follow_line_simple(floor_color)

    # PHASE 2: Zweite blaue Platte erkennen und 180° drehen
    while True:
        floor_color = sensor_floor.color
        right_color_id = sensor_right.value(0)

        if right_color_id == BLUE:
            turn_180_degrees()
            if ws is not None:
                message = {"Type": "DRIVE_TO_BASE_ANSWER", "Answer": "TRUE"}
                ws.send(json.dumps(message))
                print("DRIVE_TO_BASE_ANSWER an Server gesendet.")

            return  

        else:  # Linienverfolgung
            follow_line_simple(floor_color)

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
    driveToRoom(waitingRoom)
    
    if ws is not None:
        message = {"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"}
        ws.send(json.dumps(message))
        print("PICK_PATIENT_ANSWER an Server gesendet.")

    positionRobot = POSITION_WAITING
    print("Position Roboter in pickupPatient gesetzt auf:", positionRobot)