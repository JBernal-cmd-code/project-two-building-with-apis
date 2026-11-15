"""Shared test configuration.

Every test runs with the network blocked. Open Library must be faked by
replacing ``requests.get`` with monkeypatch, as the script tests already do.
"""

import json
import socket

import pytest
import requests


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


def make_response(status_code=200, body=None, raw=None):
    """Build a real requests.Response without making a request."""
    response = requests.Response()
    response.status_code = status_code
    response.url = "https://openlibrary.org/search.json"
    if raw is not None:
        response._content = raw
    else:
        response._content = json.dumps(body if body is not None else {}).encode()
    return response


@pytest.fixture
def fake_open_library(monkeypatch):
    """Replace the app client's ``requests.get``.

    Call it with a response body (or ``status``/``raw``) to return, or with
    ``error=`` to raise. It returns a list that records each call's arguments.
    """
    from books import openlibrary

    def install(body=None, *, status=200, raw=None, error=None):
        calls = []

        def fake_get(url, **kwargs):
            calls.append({"url": url, **kwargs})
            if error is not None:
                raise error
            return make_response(status, body, raw)

        monkeypatch.setattr(openlibrary.requests, "get", fake_get)
        return calls

    return install
