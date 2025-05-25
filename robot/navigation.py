from time import sleep
from robot.hardware import ev3_hardware, ColorValues, SpeedConstants, THRESHOLD

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

def check_and_handle_obstacle(threshold = THRESHOLD):
    """Überprüft auf Hindernis und pausiert bei Bedarf"""
    distance = ev3_hardware.sensor_ir.proximity
    if distance < threshold:
        print("Hindernis erkannt - Roboter stoppt.")
        ev3_hardware.tank_drive.off()
        while ev3_hardware.sensor_ir.proximity < threshold:  # Warte bis Hindernis entfernt ist
            sleep(0.5)
        print("Hindernis entfernt - Roboter faehrt weiter.")
    return

def follow_line_simple(floor_color=None):
    """Einfache Linienverfolgung basierend auf der Bodenfarbe."""
    check_and_handle_obstacle()

    if floor_color == ColorValues.BLACK or floor_color == ColorValues.NONE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_BLACK_L, right_speed=SpeedConstants.LINE_BLACK_R) 
    elif floor_color == ColorValues.WHITE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_WHITE_L, right_speed=SpeedConstants.LINE_WHITE_R) 
    else:
        # Bei anderen Farben (z.B. Rand der Linie, oder unerwartete Farbe) geradeaus fahren oder anpassen
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_OTHER, right_speed=SpeedConstants.LINE_OTHER) 


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
                floor_color = ev3_hardware.sensor_floor.color 
                right_color_id = ev3_hardware.sensor_right.value(0) 

                # print(">>> Nach dem Abbiegen - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

                if check_and_handle_obstacle():
                    sleep(0.1)
                    continue

                elif right_color_id == ColorValues.BLUE: 
                    print(
                        "Blaue Platte im Raum erkannt - 180 Grad drehen und auf Handy warten"
                    )
                    ev3_hardware.tank_drive.off() 
                    ev3_hardware.tank_drive.on_for_degrees( 
                        left_speed=-SpeedConstants.TURN, right_speed=SpeedConstants.TURN, degrees=406 
                    )
                    ev3_hardware.tank_drive.off() 
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

def follow_line_with_green_count(target_count, green_seen, floor_color=None):
    global last_color_green
    right_color_id = ev3_hardware.sensor_right.value(0) 

    # Nur bei Übergang von Nicht Gruen zu Gruen zählen
    if right_color_id == ColorValues.GREEN: 
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
            ev3_hardware.tank_drive.off() 
            return TARGET_ROOM_REACHED, green_seen
    else:
        last_color_green = False

    return CONTINUE_SEARCH, green_seen

def turn_into_room():
    print("Ziel erreicht - nach links abbiegen und Linie suchen")
    turn_left_90_degrees()

    # Folge der Linie bis zur blauen Platte im Raum
    while True:
        floor_color = ev3_hardware.sensor_floor.color
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE: 
            turn_180_degrees()
            return
        else:
            follow_line_simple(floor_color)

def turn_180_degrees():
    print(
        "Blaue Platte erkannt - 180 Grad drehen"
    )
    ev3_hardware.tank_drive.off() 
    ev3_hardware.tank_drive.on_for_degrees( 
        left_speed=-SpeedConstants.TURN, right_speed=SpeedConstants.TURN, degrees=406 
    )
    ev3_hardware.tank_drive.off() 
    return

def turn_left_90_degrees():
    # Dreht den Roboter nach um 90° nach links, bis er wieder Schwarz erkennt
    print("Drehe 90 Grad nach links")
    ev3_hardware.tank_drive.on_for_degrees( 
        left_speed=-SpeedConstants.TURN, right_speed=SpeedConstants.TURN, degrees=203 
    )
    ev3_hardware.tank_drive.off() 

def turn_right_90_degrees():
    # Dreht den Roboter nach um 90° nach links, bis er wieder Schwarz erkennt
    print("Drehe 90 Grad nach rechts")
    ev3_hardware.tank_drive.on_for_degrees( 
        left_speed=SpeedConstants.TURN, right_speed=-SpeedConstants.TURN, degrees=203 
    )
    ev3_hardware.tank_drive.off() 
