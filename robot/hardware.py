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

# Initialisiere die Sensoren
sensor_touch = TouchSensor()
sensor_floor = ColorSensor(address="in2")  # EV3 Color Sensor auf Boden
sensor_right = Sensor(
    address="in3", driver_name="ht-nxt-color"
)  # HiTechnic Sensor nach rechts
sensor_ir = InfraredSensor(address="in4")  # Infrarot-Sensor vorne

# Initialisiere die Motoren
tank_drive = MoveTank(OUTPUT_A, OUTPUT_D)


def color_mode_toggle():
    sensor_floor.mode = "COL-COLOR"

