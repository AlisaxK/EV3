from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.sensor import Sensor
import json
from time import sleep

# Direkter Zugriff auf Konstanten über Klassenname, z.B. ColorValues.BLACK
# Zugriff auf Hardware-Komponenten über ev3_hardware Instanz, z.B. ev3_hardware.sensor_touch

# Farbwerte
class ColorValues:
    NONE = 0
    BLACK = 1
    BLUE = 3
    GREEN = 4
    RED = 5
    WHITE = 6
    PURPLE = 7

# Geschwindigkeitskonstanten
class SpeedConstants:
    LINE_BLACK_L = 25
    LINE_BLACK_R = 22
    LINE_WHITE_L = 22
    LINE_WHITE_R = 25
    LINE_OTHER = 20
    TURN = 20
    STRAIGHT_SLOW = 20

# Abstand Threshold
THRESHOLD = 30

class EV3Hardware:
    def __init__(self):
        # Initialisiere die Sensoren
        self.sensor_touch = TouchSensor()
        self.sensor_floor = ColorSensor(address="in2")  # EV3 Color Sensor auf Boden
        self.sensor_right = Sensor(
            address="in3", driver_name="ht-nxt-color"
        )  # HiTechnic Sensor nach rechts
        self.sensor_ir = InfraredSensor(address="in4")  # Infrarot-Sensor vorne

        # Initialisiere die Motoren
        self.tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)
        
        # Setze den Modus fuer den Bodensensor
        self.sensor_floor.mode = ColorSensor.MODE_COL_COLOR

# Globale Instanz der Hardware-Klasse
ev3_hardware = EV3Hardware()

#
def wait_for_phone_removed(ws=None, timeout_seconds=5):
    print("Warte darauf, dass das Handy entfernt wird...")
    waited = 0
    while ev3_hardware.sensor_touch.is_pressed:
        sleep(0.1)
        waited += 0.1

        if waited >= timeout_seconds:
            # print("Fehler: Handy wurde nach 5 Sekunden noch nicht entfernt!")
            if ws is not None:
                message = {"message": "ERROR_PHONE_NOT_REMOVED"}
                ws.send(json.dumps(message))
                print("Fehler-Nachricht an Server gesendet: ERROR_PHONE_NOT_REMOVED")
            waited = 0
    print("Handy entfernt. Starte Raumwahl.")
    sleep(5)

def wait_for_phone_placed(ws=None, timeout_seconds=5):
    # print("Warte darauf, dass das Handy wieder platziert wird...")
    waited = 0

    while not ev3_hardware.sensor_touch.is_pressed:
        sleep(0.1)
        waited += 0.1

        if waited >= timeout_seconds:
            print("Fehler: Handy noch nicht erkannt nach 5 Sekunden!")
            if ws is not None:
                message = {"message": "ERROR_NO_PHONE_DETECTED"}
                ws.send(json.dumps(message))
                print("Fehler-Nachricht an Server gesendet: ERROR_NO_PHONE_DETECTED")
            waited = 0  # **Reset**:
    print("Handy erkannt. Roboter faehrt weiter.")
    sleep(5)