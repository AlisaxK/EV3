import unittest
from unittest.mock import MagicMock
from websocket_client import EV3WebSocketClient
from main import EV3CommandHandler


class TestWebSocketIntegration(unittest.TestCase):
    def test_ws_is_assigned_to_handler_on_open(self):
        ws_mock = MagicMock()
        handler = EV3CommandHandler(ws=None)

        # Erstelle Client und verwende die Handler-Methode
        client = EV3WebSocketClient("ws://localhost", handler.handle_command)
        # Simuliere Verbindungsaufbau
        client.on_open(ws_mock)
        self.assertIs(handler.ws, ws_mock, "WebSocket wurde nicht korrekt übergeben")


if __name__ == "__main__":
    unittest.main()
