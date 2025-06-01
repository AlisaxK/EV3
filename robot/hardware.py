from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.sensor import Sensor
import json
from time import sleep

class ColorValues:
    NONE = 0
    BLACK = 1
    BLUE = 3
    GREEN = 4
    RED = 5
    WHITE = 6
    PURPLE = 7

class SpeedConstants:
    LINE_BLACK_L = 25
    LINE_BLACK_R = 24
    LINE_WHITE_L = 24
    LINE_WHITE_R = 25
    LINE_OTHER = 20
    TURN = 20
    STRAIGHT_SLOW = 20

THRESHOLD = 30

class EV3Hardware:
    def __init__(self):
        self.sensor_touch = TouchSensor()
        self.sensor_floor = ColorSensor(address="in2")  # EV3 Color Sensor auf Boden
        self.sensor_right = Sensor(
            address="in3", driver_name="ht-nxt-color"
        )  # HiTechnic Sensor nach rechts
        self.sensor_ir = InfraredSensor(address="in4")  # Infrarot-Sensor vorne

        self.tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)
        
        # Setze den Modus fuer den Bodensensor
        self.sensor_floor.mode = ColorSensor.MODE_COL_COLOR

ev3_hardware = EV3Hardware()

def wait_for_phone_removed(ws=None, timeout_seconds=10):
    waited = 0
    while ev3_hardware.sensor_touch.is_pressed:
        sleep(0.1)
        waited += 0.1

        if waited >= timeout_seconds:
            if ws is not None:
                message = {"type": "ERROR_PHONE_NOT_REMOVED"}
                ws.send(json.dumps(message))
            waited = 0
    sleep(5)

def wait_for_phone_placed(ws=None, timeout_seconds=10):
    waited = 0

    while not ev3_hardware.sensor_touch.is_pressed:
        sleep(0.1)
        waited += 0.1

        if waited >= timeout_seconds:
            if ws is not None:
                message = {"type": "ERROR_NO_PHONE_DETECTED"}
                ws.send(json.dumps(message))
            waited = 0
    sleep(5)