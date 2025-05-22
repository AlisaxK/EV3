from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.sensor import Sensor
from time import sleep
import json

# Initialisiere die Sensoren
sensor_touch = TouchSensor()
sensor_floor = ColorSensor(address="in2")  # EV3 Color Sensor auf Boden
sensor_right = Sensor(
    address="in3", driver_name="ht-nxt-color"
)  # HiTechnic Sensor nach rechts
sensor_ir = InfraredSensor(address="in4")  # Infrarot-Sensor vorne

# Initialisiere die Motoren
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)

# Farbwerte fuer die Linienverfolgung
BLACK = 0
WHITE = 1
YELLOW = 6
PURPLE = 7
BLUE = 3
GREEN = 4
RED = 5

# Geschwindigkeitskonstanten
SPEED_LINE_BLACK_L = 25
SPEED_LINE_BLACK_R = 22
SPEED_LINE_WHITE_L = 22
SPEED_LINE_WHITE_R = 25
SPEED_LINE_OTHER = 20
SPEED_TURN = 20
SPEED_STRAIGHT_SLOW = 20

# Results line following
TARGET_ROOM_REACHED = "TARGET_ROOM_REACHED"
CONTINUE_SEARCH = "CONTINUE_SEARCH"
last_color_green = False

# current Position
POSITION_START = "start"
POSITION_WAITING = "waiting"
POSITION_ROOM1 = "room1"
POSITION_ROOM2 = "room2"
POSITION_ROOM3 = "room3"
positionRobot = POSITION_START


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


def check_and_handle_obstacle(threshold=30):
    """Überprüft auf Hindernis und pausiert bei Bedarf"""
    distance = sensor_ir.proximity
    if distance < threshold:
        print("Hindernis erkannt - Roboter stoppt.")
        tank_drive.off()
        while sensor_ir.proximity < threshold:  # Warte bis Hindernis entfernt ist
            sleep(0.1)
        print("Hindernis entfernt - Roboter faehrt weiter.")
        return True  # Hindernis behandelt
    return False  # Kein Hindernis oder nicht nah genug


def follow_line_simple(floor_color=None):
    """Einfache Linienverfolgung basierend auf der Bodenfarbe."""
    #floor_color = sensor_floor.color
    if floor_color == BLACK:
        tank_drive.on(left_speed=SPEED_LINE_BLACK_L, right_speed=SPEED_LINE_BLACK_R)
    elif floor_color == WHITE or floor_color == YELLOW:
        tank_drive.on(left_speed=SPEED_LINE_WHITE_L, right_speed=SPEED_LINE_WHITE_R)
    else:
        # Bei anderen Farben (z.B. Rand der Linie, oder unerwartete Farbe) geradeaus fahren oder anpassen
        tank_drive.on(left_speed=SPEED_LINE_OTHER, right_speed=SPEED_LINE_OTHER)


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

    wait_for_phone_removed(ws)

    target_index = None
    for i, val in enumerate(rooms):
        if val == 1:
            target_index = i + 1  # Zimmernummern starten bei 1
            break

    if target_index is None:
        print("Kein Zielraum angegeben Abbruch.")
        return

    print("Ziel: Zimmernummer {} - Roboter soll dort abbiegen.".format(target_index))
    from_waiting_room = positionRobot == POSITION_WAITING
    if from_waiting_room:
        print("Roboter kommt vom Warteraum und faehrt nach links")
        turn_left_to_rooms(target_index, ws)
        return

    green_count = 0

    while True:
        floor_color = sensor_floor.color
        result, green_count = follow_line_with_green_count(target_index, green_count, floor_color)

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht - nach links abbiegen und Linie suchen")
            turn_left_90_degrees()

            # Folge der Linie bis zur blauen Platte im Raum
            while True:
                right_color_id = sensor_right.value(0)

                # print(">>> Nach dem Abbiegen - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

                if check_and_handle_obstacle():
                    sleep(0.1)
                    continue

                elif right_color_id == BLUE:
                    print(
                        "Blaue Platte im Raum erkannt - 180 Grad drehen und auf Handy warten"
                    )
                    tank_drive.off()
                    tank_drive.on_for_degrees(
                        left_speed=-SPEED_TURN, right_speed=SPEED_TURN, degrees=406
                    )
                    tank_drive.off()
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
            print(floor_color)
            follow_line_simple(floor_color)
        sleep(0.1)

    return


def driveToRoomPhonePlaced(rooms, ws=None):
    global positionRobot

    if not _validate_room_list(rooms, ws):
        return

    wait_for_phone_placed(ws)

    target_index = _get_target_index(rooms)

    if target_index is None:
        print("Kein Zielraum angegeben  Abbruch.")
        return

    print("Ziel: Zimmernummer {} - Roboter soll dort abbiegen.".format(target_index))
    from_waiting_room = positionRobot == POSITION_WAITING
    if from_waiting_room:
        print("Roboter kommt vom Warteraum und faehrt nach links")
        turn_left_to_rooms(target_index, ws)
        return

    _navigate_in_target_room(target_index, ws)
    return


def _validate_room_list(rooms, ws=None):
    # print("validate_room_list")
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
        return False
    return True


def _get_target_index(rooms):
    # print("get_target_index")
    for i, val in enumerate(rooms):
        if val == 1:
            return i + 1  # Zimmernummern starten bei 1
    print("Kein Zielraum angegeben  Abbruch.")
    return None


def _navigate_in_target_room(target_index, ws=None):
    global positionRobot
    print("navigate_in_target_room")
    green_count = 0

    while True:
        result, green_count = follow_line_with_green_count(target_index, green_count)

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht - nach links abbiegen und Linie suchen")
            turn_left_90_degrees()

            # Folge der Linie bis zur blauen Platte im Raum
            while True:
                floor_color = sensor_floor.color
                right_color_id = sensor_right.value(0)

                # print(">>> Nach dem Abbiegen - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

                if check_and_handle_obstacle():
                    sleep(0.1)
                    continue

                elif right_color_id == BLUE:
                    print(
                        "Blaue Platte im Raum erkannt - 180 Grad drehen und auf Handy warten"
                    )
                    tank_drive.off()
                    tank_drive.on_for_degrees(
                        left_speed=-SPEED_TURN, right_speed=SPEED_TURN, degrees=406
                    )
                    tank_drive.off()
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
                    follow_line_simple()
                sleep(0.1)


def turn_left_to_rooms(target_index, ws=None):
    print("Verlasse das Wartezimmer und fahre in den gewaehlten Raum:", target_index)
    # PHASE 1: Erste blaue Platte erkennen und links abbiegen
    while True:
        floor_color = sensor_floor.color
        right_color_id = sensor_right.value(0)

        # print(">>> Rueckfahrt - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

        if check_and_handle_obstacle():
            sleep(0.1)
            continue

        elif right_color_id == BLUE:
            print("Erste blaue Platte erkannt - 90 Grad nach links drehen")
            tank_drive.off()
            tank_drive.on_for_degrees(
                left_speed=-SPEED_TURN, right_speed=SPEED_TURN, degrees=203
            )
            tank_drive.off()
            break  # Wechsle zu Phase 2

        else:  # Linienverfolgung
            follow_line_simple()

        sleep(0.1)

    # PHASE 2: Linie folgen und GRÜNE Platten zählen!
    green_count = 1

    while True:
        floor_color = sensor_floor.color
        result, green_count = follow_line_with_green_count(target_index, green_count)

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht - nach links abbiegen und Linie suchen")
            turn_left_90_degrees()

            # PHASE 3: Folge der Linie im Raum bis zur blauen Platte
            while True:
                floor_color = sensor_floor.color
                right_color_id = sensor_right.value(0)

                if check_and_handle_obstacle():
                    sleep(0.1)
                    continue

                elif right_color_id == BLUE:
                    print(
                        "Blaue Platte im Raum erkannt - 180 Grad drehen und auf Handy warten"
                    )
                    tank_drive.off()
                    tank_drive.on_for_degrees(
                        left_speed=-SPEED_TURN, right_speed=SPEED_TURN, degrees=406
                    )
                    tank_drive.off()
                    wait_for_phone_placed(ws)
                    return

                else:  # Linienverfolgung im Raum
                    follow_line_simple()

                sleep(0.1)


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

        # print(">>> Rueckfahrt - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

        # Hindernisvermeidung
        if check_and_handle_obstacle():
            sleep(0.1)
            continue

        elif right_color_id == BLUE:
            print("Erste blaue Platte erkannt - 90 Grad nach rechts drehen")
            tank_drive.off()
            tank_drive.on_for_degrees(
                left_speed=SPEED_TURN, right_speed=-SPEED_TURN, degrees=203
            )
            tank_drive.off()
            break  # Wechsle zu Phase 2

        else:  # Linienverfolgung
            follow_line_simple()

        sleep(0.1)

    # PHASE 2: Zweite blaue Platte erkennen und 180° drehen
    while True:
        floor_color = sensor_floor.color
        right_color_id = sensor_right.value(0)

        # print(">>> Zielsuche - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

        if check_and_handle_obstacle():
            sleep(0.1)
            continue

        elif right_color_id == BLUE:
            print(
                "Zweite blaue Platte (rechts) erkannt - Roboter dreht 180 Grad und stoppt"
            )
            tank_drive.off()
            tank_drive.on_for_degrees(
                left_speed=-SPEED_TURN, right_speed=SPEED_TURN, degrees=406
            )
            tank_drive.off()
            if ws is not None:
                message = {"Type": "DRIVE_TO_BASE_ANSWER", "Answer": "TRUE"}
                ws.send(json.dumps(message))
                print("DRIVE_TO_BASE_ANSWER an Server gesendet.")
            return

        else:  # Linienverfolgung
            follow_line_simple()

        sleep(0.1)

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
    driveToRoomPhonePlaced(waitingRoom, ws)
    wait_for_phone_removed()

    if ws is not None:
        message = {"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"}
        ws.send(json.dumps(message))
        print("PICK_PATIENT_ANSWER an Server gesendet.")

    positionRobot = POSITION_WAITING
    print("Position Roboter in pickupPatient gesetzt auf:", positionRobot)


def turn_left_90_degrees():
    # Dreht den Roboter nach um 90° nach links, bis er wieder Schwarz erkennt
    print("Drehe 90 Grad nach links")
    tank_drive.on_for_degrees(
        left_speed=-SPEED_TURN, right_speed=SPEED_TURN, degrees=203
    )
    tank_drive.off()


def follow_line_with_green_count(target_count, green_seen, floor_color=None):
    global last_color_green
    right_color_id = sensor_right.value(0)

    # print(">>> Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}, Gruen gezaehlt: {}".format(floor_color, right_color_id, distance, green_seen))

    if check_and_handle_obstacle():
        return CONTINUE_SEARCH, green_seen

    # Nur bei Übergang von Nicht Gruen zu Gruen zählen
    if right_color_id == GREEN:
        if not last_color_green:
            green_seen += 1
            print(
                "Uebergang zu Gruen erkannt. Gruen Platte Nummer {} gezaehlt.".format(
                    green_seen
                )
            )
        last_color_green = True
        if green_seen == target_count:
            print("Ziel erreicht. Abbiegen.")
            tank_drive.off()
            return TARGET_ROOM_REACHED, green_seen
    else:
        last_color_green = False

    return CONTINUE_SEARCH, green_seen
