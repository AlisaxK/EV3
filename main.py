#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from time import sleep

# Initialisiere die Sensoren
sensor_touch = TouchSensor()
sensor_color = ColorSensor(address='in2')

# Initialisiere die Motoren
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)

# Farbwerte für die Linienverfolgung
BLACK = 0  # Anpassung je nach Umgebungslicht nötig
WHITE = 1
YELLOW = 6
PURPLE = 7
THRESHOLD = (BLACK + WHITE) / 2  # Schwellenwert für die Linie

# Räume die angesteuert werden sollen: Wartezimmer, Zimmer 1, Zimmer 2, Zimmer 3
room ={0, 0, 0, 1}

# Benutzerwahl für das Abbiegeverhalten an der Kreuzung
#choice = input("Soll der Roboter bei GELB (1) oder bei LILA (2) abbiegen? (1/2): ")
choice = "2"

def driveToRoom(room):
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

    while True:
        result = follow_line()

        if result == "YELLOW":
            print("GELB erkannt. Weiterfahren...")
            continue  # Nur weiterfahren, nichts tun

        elif result == "PURPLE":
            print("LILA erkannt. Links abbiegen zum Raum.")
            turn_left_until_black()
            print("Zielraum erreicht.")
            tank_drive.off()
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

def follow_line():
    #while sensor_touch.is_pressed:
        color = sensor_color.color
        

        # Kreuzungserkennung
        if color == YELLOW and choice == "1":
            print("GELB erkannt! Abbiegen nach links.")
            tank_drive.off()
           # turn_left_until_black()
        
        # vorbei fahren an gelb, wenn zweite kreuzung
        elif color == YELLOW and choice == "2":
            print("vorbeifahren")
            tank_drive.off()
            tank_drive.on_for_seconds(left_speed=20, right_speed=20, seconds=2)
            return "YELLOW" #raus aus follow_line sonst korrigiert er nach rechts
           
        
        elif color == PURPLE and choice == "2":
            print("LILA erkannt! Abbiegen nach links.")
            tank_drive.off()
            turn_left_until_black()

        if color == BLACK:
            print("schwarz erkannt nur leicht korrigieren rechts")
            tank_drive.on(left_speed=10, right_speed=15)
        elif color == WHITE:
            print("weiss erkannt leicht korrigieren links")
            tank_drive.on(left_speed=15, right_speed=10)
        else:
            print("unklare Farbe (Zwischenbereich), fahre geradeaus")
            tank_drive.on(left_speed=10, right_speed=10)
    

try:
    print("Druecke den Touch-Sensor fuer 5 sekunden, um den Roboter starten zu lassen.")
    driveToRoom(room)

except KeyboardInterrupt:
    print("Test beendet.")
    tank_drive.off()
