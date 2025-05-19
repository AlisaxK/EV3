import json
from commands import DRIVE_TO_ROOM, DRIVE_TO_BASE, PICK_PATIENT
from robot_actions import driveToRoom, driveToBase, pickupPatientFromWaitingRoom


class EV3CommandHandler:
    def __init__(self, ws):
        self.ws = ws
        self.busy = False

    def handle_command(self, command):
        if self.busy:
            print("Roboter ist beschäftigt. Ignoriere Befehl:", command)
            self.ws.send(
                json.dumps(
                    {
                        "Type": "status",
                        "message": "busy",
                        "rejected_command": command.get("Type"),
                    }
                )
            )
            return

        self.busy = True
        action = command.get("Type")

        try:
            if action == DRIVE_TO_ROOM:
                rooms = command.get("Target", [0, 0, 0, 0])
                if isinstance(rooms, str):
                    try:
                        rooms = json.loads(rooms)
                    except json.JSONDecodeError:
                        rooms = []
                driveToRoom(rooms, self.ws)  # self.ws übergeben

            elif action == DRIVE_TO_BASE:
                driveToBase(self.ws)

            elif action == PICK_PATIENT:
                pickupPatientFromWaitingRoom(self.ws)

            else:
                print("Unbekannter Befehl:", action)
                self.ws.send(json.dumps({"Type": "error", "Answer": "unknown_command"}))

        except Exception as e:
            print("Fehler bei Ausführung:", e)
            self.ws.send(json.dumps({"Type": "error", "Answer": str(e)}))

        finally:
            self.busy = False
