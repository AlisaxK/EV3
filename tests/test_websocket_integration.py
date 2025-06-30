import unittest
from unittest.mock import MagicMock
from ws_robot.websocket_client import EV3WebSocketClient
from ws_robot.websocket_handler import EV3CommandHandler


class TestWebSocketIntegration(unittest.TestCase):
    def test_ws_is_assigned_to_handler_on_open(self):
        ws_mock = MagicMock()
        handler = EV3CommandHandler(ws=None)

        client = EV3WebSocketClient("ws://localhost", handler.handle_command)

        client.on_open(ws_mock)
        self.assertIs(handler.ws, ws_mock, "WebSocket wurde nicht korrekt übergeben")


if __name__ == "__main__":
    unittest.main()
