from time import sleep
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.sensor import Sensor

# Farbwerte fuer die Linienverfolgung
NONE = 0
BLACK = 1
BLUE = 3
GREEN = 4
RED = 5
WHITE = 6
PURPLE = 7

# Geschwindigkeitskonstanten
SPEED_LINE_BLACK_L = 25
SPEED_LINE_BLACK_R = 22
SPEED_LINE_WHITE_L = 22
SPEED_LINE_WHITE_R = 25
SPEED_LINE_OTHER = 20
SPEED_TURN = 20
SPEED_STRAIGHT_SLOW = 20

# Abstand Threshold
THRESHOLD=30

# Initialisiere die Sensoren
sensor_touch = TouchSensor()
sensor_floor = ColorSensor(address="in2")# EV3 Color Sensor auf Boden
sensor_right = Sensor(
    address="in3", driver_name="ht-nxt-color"
)  # HiTechnic Sensor nach rechts
sensor_ir = InfraredSensor(address="in4")  # Infrarot-Sensor vorne

# Initialisiere die Motoren
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)
sensor_floor.mode = "COL-COLOR"


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
    distance = sensor_ir.proximity
    if distance < threshold:
        print("Hindernis erkannt - Roboter stoppt.")
        tank_drive.off()
        while sensor_ir.proximity < threshold:  # Warte bis Hindernis entfernt ist
            sleep(0.5)
        print("Hindernis entfernt - Roboter faehrt weiter.")
    return


def follow_line_simple(floor_color=None):
    """Einfache Linienverfolgung basierend auf der Bodenfarbe."""
    check_and_handle_obstacle()

    if floor_color == BLACK or floor_color == NONE:
        tank_drive.on(left_speed=SPEED_LINE_BLACK_L, right_speed=SPEED_LINE_BLACK_R)
    elif floor_color == WHITE:
        tank_drive.on(left_speed=SPEED_LINE_WHITE_L, right_speed=SPEED_LINE_WHITE_R)
    else:
        # Bei anderen Farben (z.B. Rand der Linie, oder unerwartete Farbe) geradeaus fahren oder anpassen
        tank_drive.on(left_speed=SPEED_LINE_OTHER, right_speed=SPEED_LINE_OTHER)


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

def follow_line_with_green_count(target_count, green_seen, floor_color=None):
    global last_color_green
    right_color_id = sensor_right.value(0)

    # print(">>> Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}, Gruen gezaehlt: {}".format(floor_color, right_color_id, distance, green_seen))

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