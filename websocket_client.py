from websocket import WebSocketApp
from threading import Thread
import json
from time import sleep

websocket.enableTrace(True) # for Debugging
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
        print("WebSocket-Verbindung mit Roboter geschlossen")

    def on_open(self, ws):
        print("WebSocket-Verbindung geöffnet")
        def delayed_send():
            sleep(1)  # Wichtiger: 1 Sekunde
            try:
                ws.send("ro")
            except Exception as e:
                print("Fehler beim Senden:", e)
        Thread(target=delayed_send).start()

    def start(self):
        def run():
            while True:
                print("Versuche Verbindung zum Server...")
                self.ws = WebSocketApp(self.url,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close,
                                    on_open=self.on_open)
                try:
                    self.ws.run_forever()
                except Exception as e:
                    print("Fehler bei run_forever:", e)

                print("Verbindung getrennt warte 5 Sekunden und versuche erneut...")
                sleep(5)

        thread = Thread(target=run, daemon=True)
        thread.start()
