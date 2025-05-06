import pytest
from unittest.mock import MagicMock
from websocket import WebSocketApp


@pytest.fixture
def mock_ws():
    # returns mock object for WebSocketApp
    return MagicMock(spec=WebSocketApp)


@pytest.fixture
def mock_callback():
    # returns MagicMock Callback
    return MagicMock()
