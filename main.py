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

# Benutzerwahl für das Abbiegeverhalten an der Kreuzung
choice = input("Soll der Roboter bei GELB (1) oder bei LILA (2) abbiegen? (1/2): ")

def turn_left_until_black():
    """ Dreht den Roboter nach links, bis er wieder Schwarz erkennt """
    tank_drive.on(left_speed=-10, right_speed=25)  # Korrigiert das Linksdrehen
    while sensor_color.color != BLACK:
        sleep(0.1)
    tank_drive.off()

def follow_line():
    while sensor_touch.is_pressed:
        color = sensor_color.color
        
        if color <= THRESHOLD:  # Falls schwarz, nach rechts korrigieren
            tank_drive.on(left_speed=5, right_speed=25)
        else:  # Falls weiß, nach links korrigieren
            tank_drive.on(left_speed=25, right_speed=10)
        
        # Kreuzungserkennung
        if color == YELLOW and choice == "1":
            print("GELB erkannt! Abbiegen nach links.")
            tank_drive.off()
            turn_left_until_black()
        
        elif color == YELLOW and choice == "2":
            print("GELB erkannt! Geradeaus für 0.5 Sekunden.")
            tank_drive.on_for_seconds(left_speed=20, right_speed=20, seconds=0.5)
        
        elif color == PURPLE and choice == "2":
            print("LILA erkannt! Abbiegen nach links.")
            tank_drive.off()
            turn_left_until_black()
        
        sleep(0.1)
    
    # Falls der Touch-Sensor nicht gedrückt wird, stoppt der Roboter
    tank_drive.off()

try:
    print("Druecke den Touch-Sensor, um den Roboter starten zu lassen.")
    while True:
        if sensor_touch.is_pressed:
            follow_line()
        else:
            tank_drive.off()
        sleep(0.1)
except KeyboardInterrupt:
    print("Test beendet.")
    tank_drive.off()
