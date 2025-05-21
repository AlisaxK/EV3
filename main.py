from time import sleep
from websocket_client import EV3WebSocketClient
import json
from commands import DRIVE_TO_ROOM, DRIVE_TO_BASE, PICK_PATIENT
import robot_actions as robot
from command_handler import EV3CommandHandler


def main(ws):
    # Startpunkt des Programms
    print("Start")

    # pickupPatientFromWaitingRoom()
    robot.pickupPatientFromWaitingRoom(ws=None)
    robot.driveToRoom([0, 1, 0, 0], ws=None)
    # robot.pickupPatientFromWaitingRoom(ws=None)
    # robot.driveToBase()
    # pickupPatientFromWaitingRoom(ws=None)


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
        robot.tank_drive.off()
        print("Roboter beendet.")
