from websocket import WebSocketApp
from threading import Thread
import json
from time import sleep


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
        self.reconnect()

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket-Verbindung mit Roboter geschlossen")
        self.reconnect()

    def reconnect(self, delay=5):
        print("Versuche, die Verbindung wiederherzustellen")
        sleep(delay)
        self.start()

    def on_open(self, ws):
        self.ws = ws  # interne Referenz setzen

        # Übergib die WebSocket-Verbindung an den CommandHandler
        if hasattr(
            self.command_callback, "__self__"
        ):  # prüfen, ob Methode von einer Instanz kommt
            command_handler_instance = self.command_callback.__self__
            command_handler_instance.ws = ws

        def delayed_send():
            sleep(1)  # Wichtig: 1 Sekunde
            try:
                ws.send("ro")
            except Exception as e:
                print("Fehler beim Senden:", e)

        Thread(target=delayed_send).start()

    def send(self, message):
        if self.ws:
            self.ws.send(message)
        else:
            print("WebSocket ist noch nicht verbunden.")

    def start(self):
        self.ws = WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        thread = Thread(target=self.ws.run_forever, daemon=True)
        thread.start()
