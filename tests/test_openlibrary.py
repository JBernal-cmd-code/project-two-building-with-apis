"""The app's Open Library client (books/openlibrary.py), fully offline."""

import pytest
import requests

from books import openlibrary
from books.openlibrary import OpenLibraryError, SearchResult

HOBBIT_DOC = {
    "key": "/works/OL27482W",
    "title": "The Hobbit",
    "author_name": ["J.R.R. Tolkien"],
    "first_publish_year": 1937,
    "cover_i": 14627509,
    "number_of_pages_median": 310,
}


def test_sends_query_fields_limit_timeout_and_user_agent(
    fake_open_library, monkeypatch
):
    monkeypatch.setenv("CONTACT_EMAIL", "reader@example.com")
    calls = fake_open_library({"numFound": 0, "docs": []})

    openlibrary.search("the hobbit")

    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == "https://openlibrary.org/search.json"
    assert call["params"]["q"] == "the hobbit"
    assert call["params"]["limit"] == 20
    assert set(call["params"]["fields"].split(",")) == {
        "key",
        "title",
        "author_name",
        "first_publish_year",
        "cover_i",
        "number_of_pages_median",
    }
    assert call["timeout"] == 5
    assert call["headers"]["User-Agent"] == (
        "MyChapterCollection/1.0 (reader@example.com)"
    )


def test_user_agent_is_app_name_only_without_email(fake_open_library, monkeypatch):
    monkeypatch.delenv("CONTACT_EMAIL", raising=False)
    calls = fake_open_library({"numFound": 0, "docs": []})

    openlibrary.search("dune")

    assert calls[0]["headers"]["User-Agent"] == "MyChapterCollection/1.0"


def test_returns_total_and_cleaned_results(fake_open_library):
    fake_open_library({"numFound": 1234, "docs": [HOBBIT_DOC]})

    found = openlibrary.search("the hobbit")

    assert found.total == 1234
    assert found.results == [
        SearchResult(
            work_key="OL27482W",
            title="The Hobbit",
            authors="J.R.R. Tolkien",
            first_publish_year=1937,
            cover_id=14627509,
            total_pages=310,
        )
    ]
    assert found.results[0].cover_url == (
        "https://covers.openlibrary.org/b/id/14627509-M.jpg"
    )
    assert found.results[0].openlibrary_url == (
        "https://openlibrary.org/works/OL27482W"
    )


def test_joins_several_authors(fake_open_library):
    doc = HOBBIT_DOC | {"author_name": ["Terry Pratchett", "Neil Gaiman"]}
    fake_open_library({"numFound": 1, "docs": [doc]})

    result = openlibrary.search("good omens").results[0]

    assert result.authors == "Terry Pratchett, Neil Gaiman"


def test_missing_fields_become_blank_or_none(fake_open_library):
    doc = {"key": "/works/OL1W", "title": "Mystery Book"}
    fake_open_library({"numFound": 1, "docs": [doc]})

    result = openlibrary.search("mystery").results[0]

    assert result.authors == ""
    assert result.authors_display == "Unknown author"
    assert result.first_publish_year is None
    assert result.cover_id is None
    assert result.cover_url == ""
    assert result.total_pages is None


def test_skips_docs_without_a_key_or_title(fake_open_library):
    docs = [{"title": "No key"}, {"key": "/works/OL2W"}, "junk", HOBBIT_DOC]
    fake_open_library({"numFound": 4, "docs": docs})

    results = openlibrary.search("x").results

    assert [r.title for r in results] == ["The Hobbit"]


def test_no_matches_returns_empty_results(fake_open_library):
    fake_open_library({"numFound": 0, "docs": []})

    found = openlibrary.search("asdkjhqwe")

    assert found.total == 0
    assert found.results == []


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (requests.Timeout(), r"took too long to respond \(over 5 seconds\)"),
        (requests.ConnectTimeout(), "took too long to respond"),
        (requests.ConnectionError(), "Could not connect to Open Library"),
        (requests.TooManyRedirects(), "Something went wrong while searching"),
    ],
)
def test_request_errors_map_to_friendly_messages(fake_open_library, error, expected):
    fake_open_library(error=error)

    with pytest.raises(OpenLibraryError, match=expected):
        openlibrary.search("dune")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (429, "too many requests"),
        (403, "too many requests"),
        (500, "having problems right now"),
        (503, "having problems right now"),
        (404, "unexpected error"),
    ],
)
def test_http_errors_map_to_friendly_messages(fake_open_library, status, expected):
    fake_open_library(status=status)

    with pytest.raises(OpenLibraryError, match=expected):
        openlibrary.search("dune")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"raw": b"<html>not json</html>"},
        {"body": ["a", "list"]},
        {"body": {"numFound": 3}},
        {"body": {"docs": "not a list"}},
    ],
)
def test_unreadable_responses_map_to_friendly_message(fake_open_library, kwargs):
    fake_open_library(**kwargs)

    with pytest.raises(OpenLibraryError, match="could not read"):
        openlibrary.search("dune")
