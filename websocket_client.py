
from websocket import WebSocketApp
from threading import Thread
import json

class EV3WebSocketClient:
    def __init__(self, url, command_callback):
        self.url = url
        self.command_callback = command_callback
        self.ws = None

    def on_message(self, ws, message):
        print("Server-Nachricht empfangen:", message)
        try:
            command = json.loads(message)
            self.command_callback(command)
        except json.JSONDecodeError:
            print("Nachricht nicht als JSON erkannt:", message)

    def on_error(self, ws, error):
        print("WebSocket-Fehler:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket-Verbindung geschlossen")

    def on_open(self, ws):
        print("WebSocket-Verbindung geöffnet")
        ws.send("sm") # hier noch den key vom roboter einfügen
        #ws.send(json.dumps({"client": "EV3-Roboter"}))

    def start(self):
        self.ws = WebSocketApp(self.url,
                               on_message=self.on_message,
                               on_error=self.on_error,
                               on_close=self.on_close,
                               on_open=self.on_open)
        thread = Thread(target=self.ws.run_forever, daemon=True)
        thread.start()
