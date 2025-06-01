import json
from time import sleep
from robot.hardware import ev3_hardware, ColorValues, SpeedConstants, THRESHOLD, wait_for_phone_placed

TARGET_ROOM_REACHED = "TARGET_ROOM_REACHED"
CONTINUE_SEARCH = "CONTINUE_SEARCH"
last_color_green = False

POSITION_START = "start"
POSITION_WAITING = "waiting"
POSITION_ROOM1 = "room1"
POSITION_ROOM2 = "room2"
POSITION_ROOM3 = "room3"
positionRobot = POSITION_START

def check_and_handle_obstacle(threshold = THRESHOLD):
    distance = ev3_hardware.sensor_ir.proximity
    if distance < threshold:
        ev3_hardware.tank_drive.off()
        while ev3_hardware.sensor_ir.proximity < threshold:
            sleep(0.5)
    return

def follow_line_simple_to_room():
    check_and_handle_obstacle()
    floor_color = ev3_hardware.sensor_floor.color

    if floor_color == ColorValues.BLACK or floor_color == ColorValues.NONE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_BLACK_L, right_speed=SpeedConstants.LINE_BLACK_R) 
    elif floor_color == ColorValues.WHITE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_WHITE_L, right_speed=SpeedConstants.LINE_WHITE_R) 
    else:
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_OTHER, right_speed=SpeedConstants.LINE_OTHER) 

def follow_line_simple_to_base():
    check_and_handle_obstacle()
    floor_color = ev3_hardware.sensor_floor.color

    if floor_color == ColorValues.BLACK or floor_color == ColorValues.NONE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_WHITE_L, right_speed=SpeedConstants.LINE_WHITE_R) 
    elif floor_color == ColorValues.WHITE: 
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_BLACK_L, right_speed=SpeedConstants.LINE_BLACK_R) 

    else:
        ev3_hardware.tank_drive.on(left_speed=SpeedConstants.LINE_OTHER, right_speed=SpeedConstants.LINE_OTHER) 


def follow_line_with_green_count(target_count, green_seen):
    global last_color_green
    right_color_id = ev3_hardware.sensor_right.value(0) 

    if right_color_id == ColorValues.GREEN: 
        if not last_color_green:
            green_seen += 1
        last_color_green = True
        if green_seen == target_count:
            ev3_hardware.tank_drive.off() 
            return TARGET_ROOM_REACHED, green_seen
    else:
        last_color_green = False

    return CONTINUE_SEARCH, green_seen

def turn_into_room():
    turn_left_90_degrees()

    while True:
        right_color_id = ev3_hardware.sensor_right.value(0)

        if right_color_id == ColorValues.BLUE: 
            turn_180_degrees()
            return
        else:
            follow_line_simple_to_room()

def turn_180_degrees():
    ev3_hardware.tank_drive.off() 
    ev3_hardware.tank_drive.on_for_degrees( 
        left_speed=-SpeedConstants.TURN, right_speed=SpeedConstants.TURN, degrees=406 
    )
    ev3_hardware.tank_drive.off() 
    return

def turn_left_90_degrees():
    ev3_hardware.tank_drive.on_for_degrees( 
        left_speed=-SpeedConstants.TURN, right_speed=SpeedConstants.TURN, degrees=203 
    )
    ev3_hardware.tank_drive.off() 

def turn_right_90_degrees():
    ev3_hardware.tank_drive.on_for_degrees( 
        left_speed=SpeedConstants.TURN, right_speed=-SpeedConstants.TURN, degrees=203 
    )
    ev3_hardware.tank_drive.off()