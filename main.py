from time import sleep
from ws_robot.websocket_client import EV3WebSocketClient
import json
from ws_robot.commands import DRIVE_TO_ROOM, DRIVE_TO_BASE, PICK_PATIENT
import robot.hardware as hardware
import robot.navigation as navigation
import robot.task as task
from ws_robot.websocket_handler import EV3CommandHandler


def main(ws):
    # Startpunkt des Programms
    print("Start")

    task.pickupPatientFromWaitingRoom(ws=None)
    task.driveToRoom([0, 1, 0, 0], ws=None)
    task.driveToBase()

if __name__ == "__main__":
    # Starte WebSocket-Client
    websocket_url = (
        "ws://192.168.2.170:3001"  # Ersetze <SERVER_IP> mit deiner Server-IP
    )
    command_handler = EV3CommandHandler(None)
    ws_client = EV3WebSocketClient(
        websocket_url, command_handler.handle_command
    )  # handle_command als Callback
    ws_client.start()

    try:
        main(ws_client)
        while True:
            sleep(1)  # Hauptschleife aktiv halten
    except KeyboardInterrupt:
        hardware.tank_drive.off()
        print("Roboter beendet.")
