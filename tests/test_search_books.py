"""Tests for scripts/search_books.py.

These never touch the network. `requests.get` is replaced with a fake that
either returns a prepared response or raises the error we want to test.
"""

import json

import pytest
import requests

import search_books

HOBBIT = {
    "key": "/works/OL27482W",
    "title": "The Hobbit",
    "author_name": ["J.R.R. Tolkien"],
    "first_publish_year": 1937,
}


def make_response(status_code=200, body=None, raw=None):
    """Build a real requests.Response without making a request."""
    response = requests.Response()
    response.status_code = status_code
    response.url = search_books.SEARCH_URL
    if raw is not None:
        response._content = raw
    else:
        response._content = json.dumps(body if body is not None else {}).encode()
    return response


def fake_get_returning(response, calls=None):
    """Return a stand-in for requests.get that records its arguments."""

    def fake_get(url, **kwargs):
        if calls is not None:
            calls.append({"url": url, **kwargs})
        return response

    return fake_get


def fake_get_raising(error):
    """Return a stand-in for requests.get that raises the given error."""

    def fake_get(url, **kwargs):
        raise error

    return fake_get


# --- build_user_agent -------------------------------------------------------


def test_user_agent_includes_email_when_set():
    agent = search_books.build_user_agent("me@example.com")
    assert agent == "BookShelfScript/1.0 (me@example.com)"


def test_user_agent_is_app_name_only_without_email():
    assert search_books.build_user_agent("") == "BookShelfScript/1.0"


# --- format_book / format_results -------------------------------------------


def test_format_book_shows_all_fields():
    text = search_books.format_book(1, HOBBIT)
    assert text == (
        "1. The Hobbit\n"
        "   by J.R.R. Tolkien | first published 1937\n"
        "   Open Library ID: /works/OL27482W"
    )


def test_format_book_aligns_details_under_two_digit_numbers():
    lines = search_books.format_book(10, HOBBIT).splitlines()
    assert lines[0] == "10. The Hobbit"
    assert lines[1] == "    by J.R.R. Tolkien | first published 1937"
    assert lines[2] == "    Open Library ID: /works/OL27482W"


def test_format_book_joins_multiple_authors():
    book = {**HOBBIT, "author_name": ["Neil Gaiman", "Terry Pratchett"]}
    assert "by Neil Gaiman, Terry Pratchett" in search_books.format_book(1, book)


def test_format_book_handles_missing_fields():
    text = search_books.format_book(3, {})
    assert text.startswith("3. Untitled")
    assert "Unknown author" in text
    assert "unknown year" in text
    assert "None" not in text


def test_format_results_header_counts_and_numbers_books():
    results = search_books.SearchResults(total=1234, books=[HOBBIT, HOBBIT])
    text = search_books.format_results("the hobbit", results)
    assert text.startswith('Found 1,234 results for "the hobbit" (showing 2):')
    assert "\n1. The Hobbit" in text
    assert "\n2. The Hobbit" in text


def test_format_results_uses_singular_for_one_result():
    results = search_books.SearchResults(total=1, books=[HOBBIT])
    assert "Found 1 result for" in search_books.format_results("x", results)


def test_format_results_no_matches_message():
    results = search_books.SearchResults(total=0, books=[])
    text = search_books.format_results("zzqxv", results)
    assert text.startswith('No books matched "zzqxv".')


# --- search_books: successful requests --------------------------------------


def test_search_sends_query_fields_limit_timeout_and_user_agent(monkeypatch):
    calls = []
    response = make_response(body={"numFound": 0, "docs": []})
    monkeypatch.setattr(requests, "get", fake_get_returning(response, calls))

    search_books.search_books("the hobbit", "TestAgent/1.0")

    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == search_books.SEARCH_URL
    assert call["params"] == {
        "q": "the hobbit",
        "fields": search_books.FIELDS,
        "limit": search_books.RESULT_LIMIT,
    }
    assert call["headers"] == {"User-Agent": "TestAgent/1.0"}
    assert call["timeout"] == search_books.TIMEOUT_SECONDS


def test_search_returns_total_and_books(monkeypatch):
    response = make_response(body={"numFound": 57, "docs": [HOBBIT]})
    monkeypatch.setattr(requests, "get", fake_get_returning(response))

    results = search_books.search_books("the hobbit", "TestAgent/1.0")

    assert results.total == 57
    assert results.books == [HOBBIT]


def test_search_with_no_matches_returns_empty_results(monkeypatch):
    response = make_response(body={"numFound": 0, "docs": []})
    monkeypatch.setattr(requests, "get", fake_get_returning(response))

    results = search_books.search_books("zzqxv", "TestAgent/1.0")

    assert results.total == 0
    assert results.books == []


# --- search_books: failures --------------------------------------------------


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (requests.Timeout(), "took too long to respond"),
        (requests.ConnectTimeout(), "took too long to respond"),
        (requests.ConnectionError(), "Check your internet connection"),
        (requests.RequestException(), "Something went wrong"),
    ],
)
def test_search_network_errors_raise_friendly_message(monkeypatch, error, expected):
    monkeypatch.setattr(requests, "get", fake_get_raising(error))

    with pytest.raises(search_books.SearchError, match=expected):
        search_books.search_books("the hobbit", "TestAgent/1.0")


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (429, "too many requests"),
        (403, "too many requests"),
        (500, "having problems right now"),
        (503, "having problems right now"),
        (404, "unexpected error"),
    ],
)
def test_search_http_errors_raise_friendly_message(monkeypatch, status_code, expected):
    response = make_response(status_code=status_code)
    monkeypatch.setattr(requests, "get", fake_get_returning(response))

    with pytest.raises(search_books.SearchError, match=expected) as caught:
        search_books.search_books("the hobbit", "TestAgent/1.0")

    assert f"HTTP {status_code}" in str(caught.value)


@pytest.mark.parametrize(
    "raw",
    [
        b"<html>Service Unavailable</html>",  # not JSON at all
        b"[1, 2, 3]",  # JSON, but not an object
        b'{"numFound": 3}',  # object without a "docs" list
    ],
)
def test_search_unreadable_response_raises_friendly_message(monkeypatch, raw):
    response = make_response(raw=raw)
    monkeypatch.setattr(requests, "get", fake_get_returning(response))

    with pytest.raises(search_books.SearchError, match="could not read"):
        search_books.search_books("the hobbit", "TestAgent/1.0")


# --- main --------------------------------------------------------------------


def run_main(monkeypatch, inputs):
    """Run main() with typed inputs, no .env file, and no real requests."""
    typed = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(typed))
    monkeypatch.setattr(search_books, "load_dotenv", lambda *args, **kwargs: None)
    search_books.main()


def test_main_warns_when_email_missing_and_still_searches(monkeypatch, capsys):
    monkeypatch.delenv("CONTACT_EMAIL", raising=False)
    calls = []
    response = make_response(body={"numFound": 1, "docs": [HOBBIT]})
    monkeypatch.setattr(requests, "get", fake_get_returning(response, calls))

    run_main(monkeypatch, ["the hobbit", "q"])

    output = capsys.readouterr().out
    assert "CONTACT_EMAIL is not set" in output
    assert ".env.example" in output
    assert "1. The Hobbit" in output
    assert calls[0]["headers"] == {"User-Agent": "BookShelfScript/1.0"}


def test_main_uses_email_from_environment(monkeypatch, capsys):
    monkeypatch.setenv("CONTACT_EMAIL", "me@example.com")
    calls = []
    response = make_response(body={"numFound": 0, "docs": []})
    monkeypatch.setattr(requests, "get", fake_get_returning(response, calls))

    run_main(monkeypatch, ["zzqxv", ""])

    output = capsys.readouterr().out
    assert "CONTACT_EMAIL is not set" not in output
    assert 'No books matched "zzqxv"' in output
    assert calls[0]["headers"] == {"User-Agent": "BookShelfScript/1.0 (me@example.com)"}


def test_main_keeps_going_after_a_failed_request(monkeypatch, capsys):
    monkeypatch.setenv("CONTACT_EMAIL", "me@example.com")
    monkeypatch.setattr(requests, "get", fake_get_raising(requests.ConnectionError()))

    run_main(monkeypatch, ["the hobbit", "dune", "Q"])

    output = capsys.readouterr().out
    assert output.count("Check your internet connection") == 2
    assert output.rstrip().endswith("Goodbye!")


def test_main_quits_on_end_of_input(monkeypatch, capsys):
    monkeypatch.setenv("CONTACT_EMAIL", "me@example.com")

    def end_of_input(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", end_of_input)
    monkeypatch.setattr(search_books, "load_dotenv", lambda *args, **kwargs: None)

    search_books.main()

    assert "Goodbye!" in capsys.readouterr().out
