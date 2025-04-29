from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.sensor import Sensor
from time import sleep
from websocket_client import EV3WebSocketClient


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
THRESHOLD = (BLACK + WHITE) / 2  # Schwellenwert fuer die Linie

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
            print("Fehler: Handy wurde nach 5 Sekunden noch nicht entfernt!")
            if ws is not None:
                message = {"Type": "ERROR_PHONE_NOT_REMOVED"}
                ws.send(json.dumps(message))
                print("Fehler-Nachricht an Server gesendet: ERROR_PHONE_NOT_REMOVED")
            waited = 0
    print("Handy entfernt. Starte Raumwahl.")


def wait_for_phone_placed(ws=None, timeout_seconds=5):
    print("Warte darauf, dass das Handy wieder platziert wird...")
    waited = 0

    while not sensor_touch.is_pressed:
        sleep(0.1)
        waited += 0.1

        if waited >= timeout_seconds:
            print("Fehler: Handy noch nicht erkannt nach 5 Sekunden!")
            if ws is not None:
                message = {"Type": "ERROR_NO_PHONE_DETECTED"}
                ws.send(json.dumps(message))
                print("Fehler-Nachricht an Server gesendet: ERROR_NO_PHONE_DETECTED")
            waited = 0  # **Reset**:
    print("Handy erkannt. Roboter faehrt weiter.")


def driveToRoom(rooms, ws=None):
    global positionRobot
    wait_for_phone_removed(ws)

    target_index = None
    for i, val in enumerate(rooms):
        if val == 1:
            target_index = i + 1  # Zimmernummern starten bei 1
            break

    if target_index is None:
        print("Kein Zielraum angegeben – Abbruch.")
        return

    print("Ziel: Zimmernummer {} - Roboter soll dort abbiegen.".format(target_index))
    from_waiting_room = positionRobot == POSITION_WAITING
    if from_waiting_room:
        print("Roboter kommt vom Warteraum und faehrt nach links")
        turn_left_to_rooms(target_index, ws)
        return

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
                distance = sensor_ir.proximity

                # print(">>> Nach dem Abbiegen - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

                if distance < 30:
                    print("Hindernis erkannt - Roboter stoppt.")
                    tank_drive.off()
                    while sensor_ir.proximity < 30:
                        sleep(0.1)
                    print("Hindernis entfernt - Roboter faehrt weiter.")

                elif right_color_id == BLUE:
                    print(
                        "Blaue Platte im Raum erkannt - 180 Grad drehen und auf Handy warten"
                    )
                    tank_drive.off()
                    tank_drive.on_for_degrees(
                        left_speed=-20, right_speed=20, degrees=400
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
                else:
                    if floor_color == BLACK:
                        tank_drive.on(left_speed=20, right_speed=25)
                    elif floor_color == WHITE:
                        tank_drive.on(left_speed=25, right_speed=20)
                    else:
                        tank_drive.on(left_speed=20, right_speed=20)
                sleep(0.1)

    return


def driveToRoomPhonePlaced(rooms, ws=None):
    global positionRobot
    wait_for_phone_placed(ws)

    target_index = None
    for i, val in enumerate(rooms):
        if val == 1:
            target_index = i + 1  # Zimmernummern starten bei 1
            break

    if target_index is None:
        print("Kein Zielraum angegeben – Abbruch.")
        return

    print("Ziel: Zimmernummer {} - Roboter soll dort abbiegen.".format(target_index))
    from_waiting_room = positionRobot == POSITION_WAITING
    if from_waiting_room:
        print("Roboter kommt vom Warteraum und faehrt nach links")
        turn_left_to_rooms(target_index, ws)
        return

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
                distance = sensor_ir.proximity

                # print(">>> Nach dem Abbiegen - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

                if distance < 30:
                    print("Hindernis erkannt - Roboter stoppt.")
                    tank_drive.off()
                    while sensor_ir.proximity < 30:
                        sleep(0.1)
                    print("Hindernis entfernt - Roboter faehrt weiter.")

                elif right_color_id == BLUE:
                    print(
                        "Blaue Platte im Raum erkannt - 180 Grad drehen und auf Handy warten"
                    )
                    tank_drive.off()
                    tank_drive.on_for_degrees(
                        left_speed=-20, right_speed=20, degrees=400
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
                else:
                    if floor_color == BLACK:
                        tank_drive.on(left_speed=20, right_speed=25)
                    elif floor_color == WHITE:
                        tank_drive.on(left_speed=25, right_speed=20)
                    else:
                        tank_drive.on(left_speed=20, right_speed=20)
                sleep(0.1)

    return


def turn_left_to_rooms(target_index, ws=None):
    print("Verlasse das Wartezimmer und fahre in den gewaehlten Raum:", target_index)
    # PHASE 1: Erste blaue Platte erkennen und links abbiegen
    while True:
        floor_color = sensor_floor.color
        right_color_id = sensor_right.value(0)
        distance = sensor_ir.proximity

        # print(">>> Rueckfahrt - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

        # Hindernisvermeidung
        if distance < 30:
            print("Hindernis erkannt - Roboter stoppt.")
            tank_drive.off()
            while sensor_ir.proximity < 30:
                sleep(0.1)
            print("Hindernis entfernt - Roboter faehrt weiter.")

        elif right_color_id == BLUE:
            print("Erste blaue Platte erkannt - 90 Grad nach links drehen")
            tank_drive.off()
            tank_drive.on_for_degrees(left_speed=-20, right_speed=20, degrees=200)
            tank_drive.off()
            break  # Wechsle zu Phase 2

        elif floor_color == BLACK:
            tank_drive.on(left_speed=20, right_speed=25)
        elif floor_color == WHITE:
            tank_drive.on(left_speed=25, right_speed=20)
        else:
            tank_drive.on(left_speed=20, right_speed=20)

        sleep(0.1)

    # PHASE 2: Linie folgen und GRÜNE Platten zählen!
    green_count = 1

    while True:
        result, green_count = follow_line_with_green_count(target_index, green_count)

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht - nach links abbiegen und Linie suchen")
            turn_left_90_degrees()

            # PHASE 3: Folge der Linie im Raum bis zur blauen Platte
            while True:
                floor_color = sensor_floor.color
                right_color_id = sensor_right.value(0)
                distance = sensor_ir.proximity

                if distance < 30:
                    print("Hindernis erkannt - Roboter stoppt.")
                    tank_drive.off()
                    while sensor_ir.proximity < 30:
                        sleep(0.1)
                    print("Hindernis entfernt - Roboter faehrt weiter.")

                elif right_color_id == BLUE:
                    print(
                        "Blaue Platte im Raum erkannt - 180 Grad drehen und auf Handy warten"
                    )
                    tank_drive.off()
                    tank_drive.on_for_degrees(
                        left_speed=-20, right_speed=20, degrees=400
                    )
                    tank_drive.off()
                    wait_for_phone_placed(ws)
                    return

                else:
                    if floor_color == BLACK:
                        tank_drive.on(left_speed=20, right_speed=25)
                    elif floor_color == WHITE:
                        tank_drive.on(left_speed=25, right_speed=20)
                    else:
                        tank_drive.on(left_speed=20, right_speed=20)

                sleep(0.1)


def driveToBase():
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
        distance = sensor_ir.proximity

        # print(">>> Rueckfahrt - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

        # Hindernisvermeidung
        if distance < 30:
            print("Hindernis erkannt - Roboter stoppt.")
            tank_drive.off()
            while sensor_ir.proximity < 30:
                sleep(0.1)
            print("Hindernis entfernt - Roboter faehrt weiter.")

        elif right_color_id == BLUE:
            print("Erste blaue Platte erkannt - 90 Grad nach rechts drehen")
            tank_drive.off()
            tank_drive.on_for_degrees(left_speed=20, right_speed=-20, degrees=200)
            tank_drive.off()
            break  # Wechsle zu Phase 2

        elif floor_color == BLACK:
            tank_drive.on(left_speed=20, right_speed=25)
        elif floor_color == WHITE:
            tank_drive.on(left_speed=25, right_speed=20)
        else:
            tank_drive.on(left_speed=20, right_speed=20)

        sleep(0.1)

    # PHASE 2: Zweite blaue Platte erkennen und 180° drehen
    while True:
        floor_color = sensor_floor.color
        right_color_id = sensor_right.value(0)
        distance = sensor_ir.proximity

        # print(">>> Zielsuche - Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

        if distance < 30:
            print("Hindernis erkannt - Roboter stoppt.")
            tank_drive.off()
            while sensor_ir.proximity < 30:
                sleep(0.1)
            print("Hindernis entfernt - Roboter faehrt weiter.")

        elif right_color_id == BLUE:
            print(
                "Zweite blaue Platte (rechts) erkannt - Roboter dreht 180 Grad und stoppt"
            )
            tank_drive.off()
            tank_drive.on_for_degrees(left_speed=-20, right_speed=20, degrees=420)
            tank_drive.off()
            if ws is not None:
                message = {"Type": "DRIVE_TO_BASE_ANSWER", "Answer": "TRUE"}
                ws.send(json.dumps(message))
                print("DRIVE_TO_BASE_ANSWER an Server gesendet.")
            return

        elif floor_color == BLACK:
            tank_drive.on(left_speed=20, right_speed=25)
        elif floor_color == WHITE:
            tank_drive.on(left_speed=25, right_speed=20)
        else:
            tank_drive.on(left_speed=20, right_speed=20)

        sleep(0.1)

        global positionRobot
        positionRobot = POSITION_START
        print("Position zuruckgesetzt auf: ", positionRobot)


def pickupPatientFromWaitingRoom(ws=None):
    # Roboter fährt ins Wartezimmer um Patient abzuholen
    # Prüfen, ob Handy aufliegt, sonst error Code zurückgeben
    # success wenn erfolgreich
    print("Hole Patient im Wartezimmer ab")
    waitingRoom = [1, 0, 0, 0]
    driveToRoomPhonePlaced(waitingRoom, ws)

    if ws is not None:
        message = {"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"}
        ws.send(json.dumps(message))
        print("PICK_PATIENT_ANSWER an Server gesendet.")


def turn_left_90_degrees():
    # Dreht den Roboter nach um 90° nach links, bis er wieder Schwarz erkennt
    print("Drehe 90 Grad nach links")
    tank_drive.on_for_degrees(left_speed=-20, right_speed=20, degrees=200)
    tank_drive.off()


def follow_line_with_green_count(target_count, green_seen):
    global last_color_green
    floor_color = sensor_floor.color
    right_color_id = sensor_right.value(0)
    distance = sensor_ir.proximity

    # print(">>> Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}, Gruen gezaehlt: {}".format(floor_color, right_color_id, distance, green_seen))

    # Wenn Hindernis erkannt wird, stoppe
    if distance < 30:
        print("Hindernis erkannt - Roboter stoppt.")
        tank_drive.off()
        while sensor_ir.proximity < 30:
            sleep(0.1)
        print("Hindernis entfernt - Roboter faehrt weiter.")
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
            tank_drive.on_for_seconds(left_speed=15, right_speed=15, seconds=1)
            return CONTINUE_SEARCH, green_seen
    else:
        last_color_green = False

    # Linienverfolgung basierend auf Bodenfarbe
    if floor_color == BLACK:
        tank_drive.on(left_speed=20, right_speed=25)
    elif floor_color == WHITE:
        tank_drive.on(left_speed=25, right_speed=20)
    else:
        tank_drive.on(left_speed=20, right_speed=20)
    return CONTINUE_SEARCH, green_seen


def main():
    # Startpunkt des Programms
    print("Start")
    # driveToRoom([1, 0, 0, 0])
    pickupPatientFromWaitingRoom()
    driveToRoom([0, 1, 0, 0])
    # driveToBase()


class EV3CommandHandler:
    def __init__(self, ws):
        self.ws = ws
        self.busy = False

    def handle_command(self, command):
        if self.busy:
            print("Roboter ist beschäftigt. Ignoriere Befehl:", command)
            self.ws.send(
                json.dumps(
                    {
                        "type": "status",
                        "message": "busy",
                        "rejected_command": command.get("Type"),
                    }
                )
            )
            return

        self.busy = True
        action = command.get("Type")

        try:
            if action == "DRIVE_TO_ROOM":
                rooms = command.get("Target", [0, 0, 0, 0])
                driveToRoom(rooms, self.ws)  # self.ws übergeben
                self.ws.send(
                    json.dumps(
                        {  # antwort in drive to room verschieben
                            "Type": "DRIVE_TO_ROOM_ANSWER",
                            "Answer": "TRUE",
                        }
                    )
                )

            elif action == "DRIVE_TO_BASE":
                driveToBase(self.ws)
                self.ws.send(
                    json.dumps({"Type": "DRIVE_TO_BASE_ANSWER", "Answer": "TRUE"})
                )

            elif action == "PICK_PATIENT":
                PickupPatientFromWaitingRoom(self.ws)
                self.ws.send(
                    json.dumps({"Type": "PICK_PATIENT_ANSWER", "Answer": "TRUE"})
                )

            else:
                print("Unbekannter Befehl:", action)
                self.ws.send(json.dumps({"Type": "error", "Answer": "unknown_command"}))

        except Exception as e:
            print("Fehler bei Ausführung:", e)
            self.ws.send(json.dumps({"Type": "error", "Answer": str(e)}))

        finally:
            self.busy = False


if __name__ == "__main__":
    # Starte WebSocket-Client
    websocket_url = (
        "ws://192.168.2.170:3001"  # Ersetze <SERVER_IP> mit deiner Server-IP
    )
    command_handler = EV3CommandHandler(None)
    ws_client = EV3WebSocketClient(
        websocket_url, command_handler.handle_command
    )  # handle_command als Callback
    ws_client.start()

    try:
        main()
        while True:
            sleep(1)  # Hauptschleife aktiv halten
    except KeyboardInterrupt:
        tank_drive.off()
        print("Roboter beendet.")
