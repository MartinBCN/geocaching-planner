import socket

import pytest
from pytest_socket import SocketBlockedError


def _connect_to_network() -> None:
    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("127.0.0.1", 9))


def test_network_socket_is_blocked() -> None:
    with pytest.raises(SocketBlockedError):
        _connect_to_network()


@pytest.mark.enable_socket
def test_enable_socket_allows_local_socket() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass
