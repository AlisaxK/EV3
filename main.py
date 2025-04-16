#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from ev3dev2.sensor import Sensor
from time import sleep
from websocket_client import EV3WebSocketClient




# Initialisiere die Sensoren
sensor_touch = TouchSensor()
sensor_floor = ColorSensor(address='in2')     # EV3 Color Sensor auf Boden
sensor_right = Sensor(address='in3', driver_name='ht-nxt-color')  # HiTechnic Sensor nach rechts

# Initialisiere die Motoren
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)

# Farbwerte fuer die Linienverfolgung
BLACK = 0  
WHITE = 1
YELLOW = 6
PURPLE = 7
BLUE = 2
GREEN = 3
RED = 5
THRESHOLD = (BLACK + WHITE) / 2  # Schwellenwert fuer die Linie

# Raumfarben in Reihenfolge: [Raum 0, Raum 1, Raum 2, Raum 3]
room_colors = [YELLOW, PURPLE, RED, BLUE]

# Results line following
TARGET_ROOM_REACHED = "TARGET_REACHED"
CONTINUE_SEARCH = "CONTINUE_SEARCH"

def driveToRoom():
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

    # Ziel-Farbwahl durch Benutzer
    print("Waehle Ziel-Farbe: (1) Blau, (2) Gruen")
    auswahl = input("Eingabe: ")
    if auswahl == "1":
        target_color = BLUE
    elif auswahl == "2":
        target_color = GREEN
    else:
        print("Ungueltige Auswahl. Standard: Blau")
        target_color = BLUE

    print("Ziel: Farbe {} - Roboter soll dort abbiegen.".format(target_color))

    while True:
        result = follow_line(target_color, room_colors)

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht - nach links abbiegen und Linie suchen")
            turn_left_90_degrees()
            while True:
                follow_result = follow_line(target_color, room_colors)
                if follow_result == TARGET_ROOM_REACHED:
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
     """""" Dreht den Roboter nach um 90° nach links, bis er wieder Schwarz erkennt """"""
    print("Drehe 90 Grad nach links")
    tank_drive.on_for_degrees(left_speed=-20, right_speed=20, degrees=200)
    tank_drive.off()

def follow_line(target_color, all_room_colors):
    floor_color = sensor_floor.color
    right_color_id = sensor_right.value(0)

    print(">>> Bodenfarbe: {}, Rechts erkannt (ID): {}".format(floor_color, right_color_id))

    if right_color_id == target_color:
        print("Ziel-Farbblock erkannt (rechts). Biege ab.")
        tank_drive.off()
        return TARGET_ROOM_REACHED

    elif right_color_id in all_room_colors:
        print("Falsche Raumfarbe erkannt (rechts), weiterfahren")
        tank_drive.on_for_seconds(left_speed=15, right_speed=15, seconds=1)
        return CONTINUE_SEARCH

    if floor_color == BLACK:
        tank_drive.on(left_speed=10, right_speed=15)
    elif floor_color == WHITE:
        tank_drive.on(left_speed=15, right_speed=10)
    else:
        tank_drive.on(left_speed=10, right_speed=10)
    return CONTINUE_SEARCH

def main():
    print("Druecke den Touch-Sensor fuer 5 Sekunden, um den Roboter starten zu lassen.")
    driveToRoom()

try:
    if __name__ == '__main__':
        main()

except KeyboardInterrupt:
    print("Test beendet.")
    tank_drive.off()



### 
def handle_command(command):
    # Kommando vom Server empfangen und verarbeiten
    if command.get("action") == "driveToRoom":
        rooms = command.get("rooms", [0, 0, 0, 0])
        driveToRoom(rooms)
    elif action == "driveToBase":
        driveToBase()

    elif action == "PickupPatientFromWaitingRoom":
        PickupPatientFromWaitingRoom()

    else:
        print(f"Unbekannter Befehl erhalten: {action}")

if __name__ == "__main__":
    # Starte WebSocket-Client
    websocket_url = "ws://192.168.2.170:3001"  # Ersetze <SERVER_IP> mit deiner Server-IP
    ws_client = EV3WebSocketClient(websocket_url, handle_command) # handle_command als Callback
    ws_client.start()

    try:
        while True:
            sleep(1)  # Hauptschleife aktiv halten
    except KeyboardInterrupt:
        tank_drive.off()
        print("Roboter beendet.")