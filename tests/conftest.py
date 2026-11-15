"""Shared test configuration.

Every test runs with the network blocked. Open Library must be faked by
replacing ``requests.get`` with monkeypatch, as the script tests already do.
"""

import socket

import pytest


class NetworkAccessBlockedError(RuntimeError):
    """Raised when a test tries to open a real network connection.

    A RuntimeError, not an OSError or a requests error, so neither urllib3 nor
    the app's Open Library error handling can turn it into a friendly message.
    """


def _blocked(*args, **kwargs):
    raise NetworkAccessBlockedError(
        "Network access is blocked in tests. "
        "Fake requests.get with monkeypatch instead."
    )


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
