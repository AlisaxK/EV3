import unittest
from unittest.mock import Mock, patch, call, ANY
from ws_robot.websocket_client import EV3WebSocketClient
import json


class TestEV3WebSocketClient(unittest.TestCase):

    def setUp(self):
        self.mock_callback = Mock()
        self.client = EV3WebSocketClient("ws://testserver", self.mock_callback)

    def test_on_message_valid_json(self):
        message = json.dumps({"Type": "TEST_COMMAND"})
        self.client.on_message(None, message)
        self.mock_callback.assert_called_once_with({"Type": "TEST_COMMAND"})

    @patch("builtins.print")
    def test_on_message_invalid_json(self, mock_print):
        self.client.on_message(None, "not a json")
        mock_print.assert_any_call("Nachricht nicht als JSON erkannt:", "not a json")
        self.mock_callback.assert_not_called()

    @patch("builtins.print")
    def test_on_error(self, mock_print):
        self.client.on_error(None, "Test error")
        mock_print.assert_any_call("WebSocket-Fehler:", "Test error")
        mock_print.assert_any_call("Versuche, die Verbindung wiederherzustellen")

    @patch("builtins.print")
    def test_on_close(self, mock_print):
        self.client.on_close(None, 1000, "Normal closure")
        mock_print.assert_any_call("WebSocket-Verbindung mit Roboter geschlossen")
        mock_print.assert_any_call("Versuche, die Verbindung wiederherzustellen")

    @patch("ws_robot.websocket_client.Thread")
    def test_on_open_starts_thread(self, mock_thread):
        mock_ws = Mock()
        self.client.on_open(mock_ws)
        mock_thread.assert_called()

    def test_send_when_connected(self):
        mock_ws = Mock()
        self.client.ws = mock_ws
        self.client.send("test_message")
        mock_ws.send.assert_called_once_with("test_message")

    @patch("builtins.print")
    def test_send_when_not_connected(self, mock_print):
        self.client.ws = None
        self.client.send("test_message")
        mock_print.assert_called_with("WebSocket ist noch nicht verbunden.")

    @patch("ws_robot.websocket_client.Thread")
    def test_on_open_delayed_send(self, mock_thread):
        mock_ws = Mock()

        self.client.on_open(mock_ws)

        mock_thread.assert_called_once()
        target_function = mock_thread.call_args[1]["target"]

        with patch.object(mock_ws, "send") as mock_send:
            target_function()
            self.assertEqual(mock_send.call_count, 1)

            self.assertEqual(mock_send.call_args_list[0], call("ro"))

    @patch("ws_robot.websocket_client.Thread")
    @patch("builtins.print")
    def test_on_open_delayed_send_exception(self, mock_print, mock_thread):
        mock_ws = Mock()

        # Simuliere Fehler bei ws.send
        def raise_error(*args, **kwargs):
            raise Exception("TestSendError")

        mock_ws.send.side_effect = raise_error

        self.client.on_open(mock_ws)
        delayed_send_func = mock_thread.call_args[1]["target"]
        delayed_send_func()

        mock_print.assert_any_call("Fehler beim Senden:", ANY)

    @patch("ws_robot.websocket_client.Thread")
    @patch("ws_robot.websocket_client.WebSocketApp")
    def test_start_creates_websocket_and_starts_thread(
        self, mock_websocket_app, mock_thread
    ):
        mock_instance = Mock()
        mock_websocket_app.return_value = mock_instance

        self.client.start()

        mock_websocket_app.assert_called_once_with(
            self.client.url,
            on_message=self.client.on_message,
            on_error=self.client.on_error,
            on_close=self.client.on_close,
            on_open=self.client.on_open,
        )

        mock_thread.assert_called_once()
        self.assertEqual(mock_thread.call_args[1]["target"], mock_instance.run_forever)


if __name__ == "__main__":
    unittest.main()
