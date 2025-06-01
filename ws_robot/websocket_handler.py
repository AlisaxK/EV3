import json
from ws_robot.commands import DRIVE_TO_ROOM, DRIVE_TO_BASE, PICK_PATIENT
from robot.task import driveToRoom, driveToBase, pickupPatientFromWaitingRoom


class EV3CommandHandler:
    def __init__(self, ws):
        self.ws = ws
        self.busy = False

    def handle_command(self, command):
        if self.busy:
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
                driveToRoom(rooms, self.ws, phone_removed=True)

            elif action == DRIVE_TO_BASE:
                driveToBase(self.ws)

            elif action == PICK_PATIENT:
                pickupPatientFromWaitingRoom(self.ws)

            else:
                self.ws.send(json.dumps({"Type": "error", "Answer": "unknown_command"}))

        except Exception as e:
            self.ws.send(json.dumps({"Type": "error", "Answer": str(e)}))

        finally:
            self.busy = False