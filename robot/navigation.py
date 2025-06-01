import json
from time import sleep
from robot.hardware import ev3_hardware, ColorValues, SpeedConstants, THRESHOLD, wait_for_phone_placed

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

def follow_line_simple_to_room():
    """Einfache Linienverfolgung basierend auf der Bodenfarbe zum Raum."""
    check_and_handle_obstacle()
    floor_color = ev3_hardware.sensor_floor.color

    if floor_color == ColorValues.BLACK or floor_color == ColorValues.NONE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_BLACK_L, right_speed=SpeedConstants.LINE_BLACK_R) 
    elif floor_color == ColorValues.WHITE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_WHITE_L, right_speed=SpeedConstants.LINE_WHITE_R) 
    else:
        # Bei anderen Farben (z.B. Rand der Linie, oder unerwartete Farbe) geradeaus fahren oder anpassen
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_OTHER, right_speed=SpeedConstants.LINE_OTHER) 

def follow_line_simple_to_base():
    """Einfache Linienverfolgung basierend auf der Bodenfarbe zur Basis."""
    check_and_handle_obstacle()
    floor_color = ev3_hardware.sensor_floor.color

    if floor_color == ColorValues.BLACK or floor_color == ColorValues.NONE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_WHITE_L, right_speed=SpeedConstants.LINE_WHITE_R) 
    elif floor_color == ColorValues.WHITE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_BLACK_L, right_speed=SpeedConstants.LINE_BLACK_R) 

    else:
        # Bei anderen Farben (z.B. Rand der Linie, oder unerwartete Farbe) geradeaus fahren oder anpassen
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_OTHER, right_speed=SpeedConstants.LINE_OTHER) 

def _get_target_index(rooms):
    for i, val in enumerate(rooms):
        if val == 1:
            return i + 1  # Zimmernummern starten bei 1
    print("Kein Zielraum angegeben  Abbruch.")
    return None


def follow_line_with_green_count(target_count, green_seen):
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
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE: 
            turn_180_degrees()
            return
        else:
            follow_line_simple_to_room()

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
