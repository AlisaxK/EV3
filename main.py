from time import sleep
from ws_robot.websocket_client import EV3WebSocketClient
import json
from ws_robot.commands import DRIVE_TO_ROOM, DRIVE_TO_BASE, PICK_PATIENT
from robot.hardware import ev3_hardware
import robot.navigation as navigation
import robot.task as task
from ws_robot.websocket_handler import EV3CommandHandler


def main(ws):
    print("Start")

if __name__ == "__main__":
    websocket_url = (
        "ws://192.168.19.95:3001"
    )
    command_handler = EV3CommandHandler(None)
    ws_client = EV3WebSocketClient(
        websocket_url, command_handler.handle_command
    )
    ws_client.start()

    try:
        main(ws_client)
        while True:
            sleep(1)
    except KeyboardInterrupt:
        ev3_hardware.tank_drive.off()
        print("Roboter beendet.")
