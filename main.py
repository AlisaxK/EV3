#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from time import sleep
from websocket_client import EV3WebSocketClient



# Initialisiere die Sensoren
sensor_touch = TouchSensor()
sensor_color = ColorSensor(address='in2')

# Initialisiere die Motoren
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)

# Farbwerte für die Linienverfolgung
BLACK = 0  
WHITE = 1
YELLOW = 6
PURPLE = 7
BLUE = 2
GREEN = 3
RED = 5
THRESHOLD = (BLACK + WHITE) / 2  # Schwellenwert für die Linie



# Raumfarben in Reihenfolge: [Raum 0, Raum 1, Raum 2, Raum 3]
room_colors = [YELLOW, PURPLE, RED, BLUE]

# Results line following
TARGET_ROOM_REACHED = "TARGET_REACHED"
CONTINUE_SEARCH = "CONTINUE_SEARCH"

# Benutzerwahl für das Abbiegeverhalten an der Kreuzung
#choice = input("Soll der Roboter bei GELB (1) oder bei LILA (2) abbiegen? (1/2): ")
choice = "2"

def driveToRoom(rooms):
    #Roboter fährt in ein Behandlungszimmer oder in das Wartezimmer
    #Prüfung, ob Handy auf sensor liegt, sonst error Code zurückgeben
    print("Warte auf 5 Sekunden langen Druck auf den Touchsensor")

    pressed_time = 0
    while pressed_time < 5:
        if sensor_touch.is_pressed:
            sleep(1)
            pressed_time += 1
            print("{} Sekunde(n) gedrueckt".format(pressed_time))

        else:
            pressed_time = 0  # Timer zurücksetzen, wenn losgelassen

    print("Startsignal erkannt. Roboter faehrt los")

    if 1 not in rooms:
        print("kein Zielraum ausgewaehlt.")
        return
    
    target_room = rooms.index(1)
    target_color = room_colors[target_room]

    print("Ziel: Raum {} mit Farbe {}".format(target_room, target_color))

    while True:
        result = follow_line(target_color, room_colors)

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht")
            turn_left_until_black()
            break
            



def driveToBase():
    # Roboter fährt zu Ausgangspunkt zurück
    # eventuell prüfen, ob Handy auf dem Roboter liegt, sonst error Code
    print("Fahre zu Start")

def PickupPatientFromWaitingRoom():
    # Roboter fährt ins Wartezimmer um Patient abzuholen
    # Prüfen, ob Handy aufgehoben wurde, sonst error Code zurückgeben
    print("Hole Patient im Wartezimmer ab")

def turn_left_until_black():
    """ Dreht den Roboter nach links, bis er wieder Schwarz erkennt """
    tank_drive.on(left_speed=-10, right_speed=15)  # Korrigiert das Linksdrehen
    while sensor_color.color != BLACK:
        sleep(0.1)
    tank_drive.off()

def follow_line(target_color, all_room_colors):
        color = sensor_color.color
        print(">>> Erkannte Farbe: ", color)
        # Kreuzungserkennung
        if color == target_color:
            print("Ziel-Farbe erkannt. Biege ab")
            tank_drive.off()
            turn_left_until_black()
            sleep(10)
            return TARGET_ROOM_REACHED
        
        # vorbei fahren wenn nicht Zielfarbe
        elif color in all_room_colors:
            print("vorbeifahren")
            tank_drive.on_for_seconds(left_speed=20, right_speed=20, seconds=1)
            return CONTINUE_SEARCH
           
        #Linienverfolgung
        if color == BLACK:
            #print("schwarz erkannt korrigieren rechts")
            tank_drive.on(left_speed=10, right_speed=15)
        elif color == WHITE:
            #print("weiss erkannt korrigieren links")
            tank_drive.on(left_speed=15, right_speed=10)
        else:
            #print("unklare Farbe (Zwischenbereich), fahre geradeaus")
            tank_drive.on(left_speed=10, right_speed=10)
    

try:
    print("Druecke den Touch-Sensor fuer 5 sekunden, um den Roboter starten zu lassen.")
    rooms = [0, 0, 1, 0]
    driveToRoom(rooms)


      """
    print("Starte Farberkennungs-Test.")
    while True:
        color = sensor_color.color
        print("Erkannte Farbe: {}", color)
        sleep(0.5)
    """
    
    
   
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