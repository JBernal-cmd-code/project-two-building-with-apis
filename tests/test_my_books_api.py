"""Tests for scripts/my_books_api.py.

Most tests run the script against the real API views: ``requests.request`` is
replaced with a fake that sends each call through Django's test client, so no
server or network is needed. Failure tests fake ``requests.request`` directly.
"""

import argparse
import json
from urllib.parse import urlsplit

import pytest
import requests
from django.test import Client

import my_books_api
from books.models import SavedBook

PASSWORD = "a-Long-unusual-pass-42"
BASE_URL = "http://testserver"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    """Credentials come from the environment, never from a real .env file."""
    monkeypatch.setattr(my_books_api, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("API_BASE_URL", BASE_URL)
    monkeypatch.setenv("API_USERNAME", "reader")
    monkeypatch.setenv("API_PASSWORD", PASSWORD)


@pytest.fixture
def server(monkeypatch, db):
    """Route the script's HTTP calls into the Django app. Records each call."""
    client = Client()
    calls = []

    def fake_request(
        method, url, *, headers, timeout, params=None, data=None, json=None
    ):
        calls.append(
            {"method": method, "url": url, "headers": headers, "params": params}
        )
        assert timeout == my_books_api.TIMEOUT_SECONDS
        path = urlsplit(url).path
        if method == "GET":
            response = client.get(path, params or {}, headers=headers)
        elif method == "POST":
            response = client.post(path, data, headers=headers)
        elif method == "PATCH":
            response = client.patch(
                path, _dumps(json), content_type="application/json", headers=headers
            )
        else:
            raise AssertionError(f"Unexpected method {method}")
        return make_response(response.status_code, raw=response.content, url=url)

    monkeypatch.setattr(requests, "request", fake_request)
    return calls


def _dumps(value):
    # fake_request's ``json`` argument (named like requests') hides the module.
    return json.dumps(value)


def make_response(status_code=200, body=None, raw=None, url=BASE_URL):
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    response._content = raw if raw is not None else json.dumps(body).encode()
    return response


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


@pytest.fixture
def other(django_user_model):
    return django_user_model.objects.create_user(username="other", password=PASSWORD)


def save_book(owner, title, work_key, **fields):
    return SavedBook.objects.create(
        owner=owner, ol_work_key=work_key, title=title, **fields
    )


def run(capsys, *argv):
    code = my_books_api.main(list(argv))
    return code, capsys.readouterr().out


# --- Full runs against the real API -------------------------------------------


def test_default_run_lists_filtered_books_and_patches_the_first(server, reader, capsys):
    dune = save_book(
        reader,
        "Dune",
        "OL893415W",
        authors="Frank Herbert",
        status="reading",
        current_page=100,
        total_pages=400,
    )
    save_book(reader, "Anathem", "OL1W", status="reading", current_page=5)
    save_book(reader, "Emma", "OL2W", status="finished")

    code, out = run(capsys)

    assert code == 0
    assert 'Logged in as "reader"' in out
    assert "Found 2 books (Reading, sorted by title (A-Z))" in out
    assert "Emma" not in out
    # Sorted by title, so Anathem is first and is the one updated.
    assert out.index("Anathem") < out.index("Dune")
    assert "Updating book #" in out
    assert "current_page: 5 -> 15" in out
    dune.refresh_from_db()
    assert dune.current_page == 100
    assert SavedBook.objects.get(title="Anathem").current_page == 15


def test_token_is_used_after_login(server, reader, capsys):
    save_book(reader, "Dune", "OL893415W", status="reading")

    run(capsys)

    login, *rest = server
    assert login["method"] == "POST"
    assert login["url"] == f"{BASE_URL}/api/token/"
    assert "Authorization" not in login["headers"]
    token = SavedBook.objects.get().owner.auth_token.key
    assert all(c["headers"]["Authorization"] == f"Token {token}" for c in rest)
    assert server[1]["params"] == {"status": "reading", "ordering": "title"}


def test_set_status_finished_shows_auto_filled_page(server, reader, capsys):
    book = save_book(
        reader,
        "Dune",
        "OL893415W",
        status="reading",
        current_page=100,
        total_pages=400,
    )

    code, out = run(capsys, "--book-id", str(book.pk), "--set", "status=finished")

    assert code == 0
    before, after = out.split("After:")
    assert "Reading | page 100 of 400 (25%)" in before
    assert "Finished | page 400 of 400 (100%)" in after
    assert "status: 'reading' -> 'finished'" in out
    assert "current_page: 100 -> 400" in out


def test_status_any_and_ordering_are_sent(server, reader, capsys):
    save_book(reader, "Dune", "OL893415W", status="finished", rating=5)

    code, out = run(capsys, "--status", "any", "--ordering=-rating")

    assert code == 0
    assert server[1]["params"] == {"ordering": "-rating"}
    assert "Found 1 book (any status, sorted by highest rated)" in out


def test_validation_error_is_shown_and_book_is_unchanged(server, reader, capsys):
    book = save_book(reader, "Dune", "OL893415W", status="reading", total_pages=400)

    code, out = run(capsys, "--book-id", str(book.pk), "--set", "current_page=999")

    assert code == 1
    assert "The server rejected the change:" in out
    assert "current_page: Current page can't be more than total pages." in out
    book.refresh_from_db()
    assert book.current_page == 0


def test_another_users_book_is_not_found(server, reader, other, capsys):
    theirs = save_book(other, "Dune", "OL893415W", status="reading")

    code, out = run(capsys, "--book-id", str(theirs.pk), "--set", "rating=1")

    assert code == 1
    assert f"There's no book with id {theirs.pk} in your collection." in out
    theirs.refresh_from_db()
    assert theirs.rating is None


def test_empty_list_skips_the_update(server, reader, capsys):
    code, out = run(capsys)

    assert code == 0
    assert "No books match those filters (Reading, sorted by title (A-Z))." in out
    assert "No book to update." in out
    assert [c["method"] for c in server] == ["POST", "GET"]


def test_wrong_password_shows_login_failed(server, reader, monkeypatch, capsys):
    monkeypatch.setenv("API_PASSWORD", "wrong")

    code, out = run(capsys)

    assert code == 1
    assert 'Login failed for "reader"' in out
    assert "API_PASSWORD" in out
    assert len(server) == 1


# --- Failures without a server ------------------------------------------------


def test_missing_credentials_explains_setup(monkeypatch, capsys):
    monkeypatch.delenv("API_USERNAME")
    monkeypatch.setattr(requests, "request", _must_not_be_called)

    code, out = run(capsys)

    assert code == 1
    assert "API_USERNAME and API_PASSWORD are not set." in out
    assert ".env.example" in out


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (requests.ConnectionError(), "Could not connect to the Django server"),
        (requests.ConnectTimeout(), "took too long to respond"),
        (requests.RequestException("boom"), "Something went wrong"),
    ],
)
def test_network_failures_show_a_message(monkeypatch, capsys, error, expected):
    monkeypatch.setattr(requests, "request", _raise(error))

    code, out = run(capsys)

    assert code == 1
    assert expected in out


def test_server_not_running_says_how_to_start_it(monkeypatch, capsys):
    monkeypatch.setattr(requests, "request", _raise(requests.ConnectionError()))

    _, out = run(capsys)

    assert f"Could not connect to the Django server at {BASE_URL}." in out
    assert "uv run python manage.py runserver" in out


def test_non_json_response_points_to_base_url(monkeypatch, capsys):
    page = make_response(200, raw=b"<html>Not this app</html>")
    monkeypatch.setattr(requests, "request", lambda *args, **kwargs: page)

    code, out = run(capsys)

    assert code == 1
    assert "isn't JSON" in out
    assert "API_BASE_URL" in out


def test_server_error_points_to_runserver_terminal(monkeypatch, capsys):
    page = make_response(500, raw=b"")
    monkeypatch.setattr(requests, "request", lambda *args, **kwargs: page)

    code, out = run(capsys)

    assert code == 1
    assert "HTTP 500" in out
    assert "runserver terminal" in out


def _must_not_be_called(*args, **kwargs):
    raise AssertionError("No request should be made")


def _raise(error):
    def fail(*args, **kwargs):
        raise error

    return fail


# --- Helpers ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("current_page=120", ("current_page", 120)),
        ("rating=4", ("rating", 4)),
        ("rating=none", ("rating", None)),
        ("total_pages=", ("total_pages", None)),
        ("status=finished", ("status", "finished")),
        ("notes=Loved it = really", ("notes", "Loved it = really")),
    ],
)
def test_parse_assignment(text, expected):
    assert my_books_api.parse_assignment(text) == expected


@pytest.mark.parametrize(
    "text", ["title=New", "current_page", "current_page=lots", "notes"]
)
def test_parse_assignment_rejects_bad_input(text):
    with pytest.raises(argparse.ArgumentTypeError):
        my_books_api.parse_assignment(text)


def test_bad_set_option_exits_with_usage_error(capsys):
    with pytest.raises(SystemExit) as exit_info:
        my_books_api.main(["--set", "title=New"])

    assert exit_info.value.code == 2
    assert "FIELD=VALUE" in capsys.readouterr().err


def test_default_change_stops_at_the_last_page():
    book = {"current_page": 395, "total_pages": 400}
    assert my_books_api.default_change(book) == ("current_page", 400)


def test_default_change_without_total_pages():
    assert my_books_api.default_change({"current_page": 0}) == ("current_page", 10)


def test_format_book_handles_missing_fields():
    text = my_books_api.format_book({"id": 3})
    assert text.startswith("#3  Untitled")
    assert "Unknown author" in text
    assert "not rated" in text
    assert "None" not in text


def test_format_book_truncates_long_notes():
    text = my_books_api.format_book({"id": 1, "notes": "x" * 200})
    notes_line = text.splitlines()[-1]
    assert notes_line.endswith("...")
    assert len(notes_line) <= len("    Notes: ") + my_books_api.NOTES_PREVIEW_LENGTH


def test_format_changes_with_nothing_changed():
    book = {"status": "reading", "current_page": 4}
    assert my_books_api.format_changes(book, book).startswith("Nothing changed")
