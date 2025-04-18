from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.sensor import Sensor
from time import sleep
#from websocket_client import EV3WebSocketClient




# Initialisiere die Sensoren
sensor_touch = TouchSensor()
sensor_floor = ColorSensor(address='in2')     # EV3 Color Sensor auf Boden
sensor_right = Sensor(address='in3', driver_name='ht-nxt-color')  # HiTechnic Sensor nach rechts
sensor_ir = InfraredSensor(address='in4')     # Infrarot-Sensor vorne

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
last_color_blue = False

def driveToRoom(rooms, ws=None): #ws=None übergeben, um Status zu senden
    #Roboter fährt in ein Behandlungszimmer oder in das Wartezimmer
    #Prüfung, ob Handy auf sensor liegt, sonst error Code zurückgeben „no_phone_detected"
    # Status success wenn erfolgreich
    print("Warte auf 5 Sekunden langen Druck auf den Touchsensor")
    pressed_time = 0
    while pressed_time < 5:
        if sensor_touch.is_pressed:
            sleep(1)
            pressed_time += 1
            print("{} Sekunde(n) gedrueckt".format(pressed_time))
        else:
            pressed_time = 0 # Timer zurücksetzen, wenn losgelassen

    print("Startsignal erkannt. Roboter faehrt los")

    # Ziel-Zimmerwahl durch Benutzer mit Wiederholung bei ungueltiger Eingabe
    target_index = None
    while target_index is None:
        print("Waehle Ziel-Zimmer: (1) Zimmer 1, (2) Zimmer 2, (3) Zimmer 3, (4) Zimmer 4")
        eingabe = input("Eingabe: ")
        if eingabe in ["1", "2", "3", "4"]:
            target_index = int(eingabe)
        else:
            print("Ungueltige Eingabe. Bitte 1 bis 4 waehlen.")

    print("Ziel: Zimmernummer {} - Roboter soll dort abbiegen.".format(target_index))
    blue_count = 0

    while True:
        result, blue_count = follow_line_with_blue_count(target_index, blue_count)

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht - nach links abbiegen und Linie suchen")
            turn_left_90_degrees()
            while True:
                result, blue_count = follow_line_with_blue_count(target_index, blue_count)
                if result == TARGET_ROOM_REACHED:
                    print("Zweites Ziel erreicht oder erneut gleiche Farbe erkannt.")
                    break
            break

def driveToBase():
    # Roboter fährt zu Ausgangspunkt zurück
    # eventuell prüfen, ob Handy auf dem Roboter liegt, sonst error Code „no_phone_detected“
    # success wenn erfolgreich
    print("Fahre zu Start")

def PickupPatientFromWaitingRoom():
    # Roboter fährt ins Wartezimmer um Patient abzuholen
    # Prüfen, ob Handy aufgehoben wurde, sonst error Code zurückgeben  „phone_not_removed“ 
    # success wenn erfolgreich
    print("Hole Patient im Wartezimmer ab")

def turn_left_90_degrees():
    '''Dreht den Roboter nach um 90° nach links, bis er wieder Schwarz erkennt'''
    print("Drehe 90 Grad nach links")
    tank_drive.on_for_degrees(left_speed=-20, right_speed=20, degrees=200)
    tank_drive.off()

def follow_line_with_blue_count(target_count, blue_seen):
    global last_color_blue
    floor_color = sensor_floor.color
    right_color_id = sensor_right.value(0)
    distance = sensor_ir.proximity

    print(">>> Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}, Blau gezaehlt: {}".format(floor_color, right_color_id, distance, blue_seen))

    # Wenn Hindernis erkannt wird, stoppe
    if distance < 30:
        print("Hindernis erkannt - Roboter stoppt.")
        tank_drive.off()
        while sensor_ir.proximity < 30:
            sleep(0.1)
        print("Hindernis entfernt - Roboter faehrt weiter.")
        return CONTINUE_SEARCH, blue_seen

    # Nur bei Übergang von Nicht Blaue zu Blau zählen
    if right_color_id == BLUE:
        if not last_color_blue:
            blue_seen += 1
            print("Uebergang zu Blau erkannt. Blaue Platte Nummer {} gezaehlt.".format(blue_seen))
        last_color_blue = True
        if blue_seen == target_count:
            print("Ziel erreicht. Abbiegen.")
            tank_drive.off()
            return TARGET_ROOM_REACHED, blue_seen
        else:
            tank_drive.on_for_seconds(left_speed=15, right_speed=15, seconds=1)
            return CONTINUE_SEARCH, blue_seen
    else:
        last_color_blue = False

    # Linienverfolgung basierend auf Bodenfarbe
    if floor_color == BLACK:
        tank_drive.on(left_speed=10, right_speed=15)
    elif floor_color == WHITE:
        tank_drive.on(left_speed=15, right_speed=10)
    else:
        tank_drive.on(left_speed=10, right_speed=10)
    return CONTINUE_SEARCH, blue_seen

def main():
    # Startpunkt des Programms
    print("Druecke den Touch-Sensor fuer 5 Sekunden, um den Roboter starten zu lassen.")
    driveToRoom([0, 0, 0, 0])

try:
    if __name__ == '__main__':
        main()

except KeyboardInterrupt:
    print("Test beendet.")
    tank_drive.off()



### 

class EV3CommandHandler:
    def __init__(self, ws):
        self.ws = ws
        self.busy = False

    def handle_command(self, command):
        if self.busy:
            print("Roboter ist beschäftigt. Ignoriere Befehl:", command)
            self.ws.send(json.dumps({
                "type": "status",
                "message": "busy",
                "rejected_command": command.get("action")
            }))
            return

        self.busy = True
        action = command.get("action")

        try:
            if action == "driveToRoom":
                rooms = command.get("rooms", [0,0,0,0])
                driveToRoom(rooms, ws=None) # self.ws übergeben
                self.ws.send(json.dumps({
                "type": "info",
                "message": "driveToRoom"
                }))

            elif action == "driveToBase":
                driveToBase()
                self.ws.send(json.dumps({"type": "info", "message": "driveToBase"}))

            elif action == "PickupPatientFromWaitingRoom":
                PickupPatientFromWaitingRoom()
                self.ws.send(json.dumps({"type": "info", "message": "PickupPatientFromWaitingRoom"}))

            else:
                print("Unbekannter Befehl:", action)
                self.ws.send(json.dumps({"type": "error", "message": "unknown_command"}))

        except Exception as e:
            print("Fehler bei Ausführung:", e)
            self.ws.send(json.dumps({"type": "error", "message": str(e)}))

        finally:
            self.busy = False

if __name__ == "__main__":
    # Starte WebSocket-Client
    websocket_url = "ws://<SERVER_IP>:3001"  # Ersetze <SERVER_IP> mit deiner Server-IP
    command_handler= EV3CommandHandler(None)
    ws_client = EV3WebSocketClient(websocket_url, command_handler.handle_command) # handle_command als Callback
    ws_client.start()

    try:
        while True:
            sleep(1)  # Hauptschleife aktiv halten
    except KeyboardInterrupt:
        tank_drive.off()
        print("Roboter beendet.")