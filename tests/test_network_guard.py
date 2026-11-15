"""The test suite must never reach the real network.

An autouse fixture in conftest.py blocks sockets, so a test that forgets to
fake Open Library fails loudly instead of quietly calling the real API.
"""

import pytest
import requests


def test_unfaked_network_call_fails_loudly():
    # Loopback port 9 (discard) keeps this harmless even before the guard exists.
    with pytest.raises(BaseException) as excinfo:
        requests.get("http://127.0.0.1:9/", timeout=1)

    assert "Network access is blocked in tests" in str(excinfo.value)
    # It must not look like an ordinary requests error, or the app's
    # friendly-error handling would swallow it and the test would pass anyway.
    assert not isinstance(excinfo.value, requests.RequestException)
