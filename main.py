from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.sensor import Sensor
from time import sleep

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
BLUE = 2
GREEN = 3
RED = 5
THRESHOLD = (BLACK + WHITE) / 2  # Schwellenwert fuer die Linie

# Results line following
TARGET_ROOM_REACHED = "TARGET_ROOM_REACHED"
CONTINUE_SEARCH = "CONTINUE_SEARCH"

def driveToRoom():
    # Roboter fährt in ein Behandlungszimmer oder in das Wartezimmer
    # Prüfung, ob Handy auf Sensor liegt, sonst Error-Code zurückgeben
    # Warte auf 5 Sekunden langen Druck auf den Touchsensor
    # print("Warte auf 5 Sekunden langen Druck auf den Touchsensor")
    # pressed_time = 0
    # while pressed_time < 5:
    #     if sensor_touch.is_pressed:
    #         sleep(1)
    #         pressed_time += 1
    #         print("{} Sekunde(n) gedrueckt".format(pressed_time))
    #     else:
    #         pressed_time = 0

    print("Startsignal erkannt. Roboter faehrt los")

    # Ziel-Farbwahl durch Benutzer mit Wiederholung bei ungueltiger Eingabe
    target_color = None
    while target_color is None:
        print("Waehle Ziel-Farbe: (1) Blau, (2) Gelb")
        auswahl = input("Eingabe: ")
        if auswahl == "1":
            target_color = BLUE
        elif auswahl == "2":
            target_color = YELLOW
        else:
            print("Ungueltige Auswahl. Bitte erneut eingeben.")

    print("Ziel: Farbe {} - Roboter soll dort abbiegen.".format(target_color))

    while True:
        result = follow_line(target_color, [YELLOW, PURPLE, RED, BLUE, GREEN])

        if result == TARGET_ROOM_REACHED:
            print("Ziel erreicht - nach links abbiegen und Linie suchen")
            turn_left_90_degrees()
            while True:
                follow_result = follow_line(target_color, [YELLOW, PURPLE, RED, BLUE, GREEN])
                if follow_result == TARGET_ROOM_REACHED:
                    print("Zweites Ziel erreicht oder erneut gleiche Farbe erkannt.")
                    break
            break

def driveToBase():
    # Roboter fährt zu Ausgangspunkt zurück
    # eventuell prüfen, ob Handy auf dem Roboter liegt, sonst Error-Code
    print("Fahre zu Start")

def PickupPatientFromWaitingRoom():
    # Roboter fährt ins Wartezimmer um Patient abzuholen
    # Prüfen, ob Handy aufgehoben wurde, sonst Error-Code zurückgeben
    print("Hole Patient im Wartezimmer ab")

def turn_left_90_degrees():
    # Dreht den Roboter um 90° nach links
    print("Drehe 90 Grad nach links")
    tank_drive.on_for_degrees(left_speed=-20, right_speed=20, degrees=200)
    tank_drive.off()

def follow_line(target_color, all_room_colors):
    floor_color = sensor_floor.color
    right_color_id = sensor_right.value(0)
    distance = sensor_ir.proximity

    print(">>> Bodenfarbe: {}, Rechts erkannt (ID): {}, Distanz: {}".format(floor_color, right_color_id, distance))

    # Wenn Hindernis erkannt wird, stoppe
    if distance < 30:
        print("Hindernis erkannt - Roboter stoppt.")
        tank_drive.off()
        while sensor_ir.proximity < 30:
            sleep(0.1)
        print("Hindernis entfernt - Roboter faehrt weiter.")
        return CONTINUE_SEARCH

    # Prüfe ob Ziel-Farbblock erkannt wurde
    if right_color_id == target_color:
        print("Ziel-Farbblock erkannt (rechts). Biege ab.")
        tank_drive.off()
        return TARGET_ROOM_REACHED

    # Falsche Raumfarbe erkannt – weiterfahren
    elif right_color_id in all_room_colors:
        print("Falsche Raumfarbe erkannt (rechts), weiterfahren")
        tank_drive.on_for_seconds(left_speed=15, right_speed=15, seconds=1)
        return CONTINUE_SEARCH

    # Linienverfolgung basierend auf Bodenfarbe
    if floor_color == BLACK:
        tank_drive.on(left_speed=10, right_speed=15)
    elif floor_color == WHITE:
        tank_drive.on(left_speed=15, right_speed=10)
    else:
        tank_drive.on(left_speed=10, right_speed=10)
    return CONTINUE_SEARCH

def main():
    # Startpunkt des Programms
    print("Druecke den Touch-Sensor fuer 5 Sekunden, um den Roboter starten zu lassen.")
    driveToRoom()

try:
    if __name__ == '__main__':
        main()

except KeyboardInterrupt:
    print("Test beendet.")
    tank_drive.off()
