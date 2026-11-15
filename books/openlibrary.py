"""The app's Open Library search client.

Modeled on ``scripts/search_books.py`` but kept separate from it, so the
graded script never changes. Only the search page calls this module: one
request per search, no retries, no caching.
"""

import os
from dataclasses import dataclass

import requests

from .models import COVER_URL, normalize_work_key

SEARCH_URL = "https://openlibrary.org/search.json"
WORK_URL = "https://openlibrary.org/works/{work_key}"
APP_NAME = "MyChapterCollection/1.0"
TIMEOUT_SECONDS = 5
RESULT_LIMIT = 20
# Ask only for the fields the app shows or saves, so responses stay small.
FIELDS = "key,title,author_name,first_publish_year,cover_i,number_of_pages_median"

UNREADABLE_MESSAGE = (
    "Open Library sent back a response we could not read. Try again later."
)


class OpenLibraryError(Exception):
    """A failed search. The message is written to be shown to the user."""


@dataclass(frozen=True)
class SearchResult:
    """One display-ready search result. Missing fields are blank or None."""

    work_key: str
    title: str
    authors: str
    first_publish_year: int | None
    cover_id: int | None
    total_pages: int | None

    @property
    def authors_display(self):
        return self.authors or "Unknown author"

    @property
    def cover_url(self):
        if self.cover_id is None:
            return ""
        return COVER_URL.format(cover_id=self.cover_id)

    @property
    def openlibrary_url(self):
        """The work's page on Open Library, for reading more before saving."""
        return WORK_URL.format(work_key=self.work_key)


@dataclass(frozen=True)
class SearchResults:
    total: int
    results: list[SearchResult]


def build_user_agent(email=None):
    """App name, plus the contact email from the environment when it is set."""
    if email is None:
        email = os.environ.get("CONTACT_EMAIL", "")
    email = email.strip()
    return f"{APP_NAME} ({email})" if email else APP_NAME


def describe_http_error(status_code):
    if status_code in (403, 429):
        return (
            "Open Library says we are sending too many requests "
            f"(HTTP {status_code}). Wait a moment and try again."
        )
    if status_code >= 500:
        return (
            f"Open Library is having problems right now (HTTP {status_code}). "
            "Try again in a few minutes."
        )
    return (
        f"Open Library returned an unexpected error (HTTP {status_code}). "
        "Try a different search, or try again later."
    )


def _positive_int(value):
    """Keep whole numbers above zero; anything else becomes None."""
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _clean(doc):
    """Turn one raw search doc into a SearchResult, or None if it can't be saved."""
    if not isinstance(doc, dict):
        return None
    work_key = normalize_work_key(doc.get("key"))
    title = doc.get("title")
    if not isinstance(work_key, str) or not work_key:
        return None
    if not isinstance(title, str) or not title.strip():
        return None
    names = doc.get("author_name")
    if not isinstance(names, list):
        names = []
    year = doc.get("first_publish_year")
    return SearchResult(
        work_key=work_key,
        title=title.strip(),
        authors=", ".join(n for n in names if isinstance(n, str) and n),
        first_publish_year=year if isinstance(year, int) else None,
        cover_id=_positive_int(doc.get("cover_i")),
        total_pages=_positive_int(doc.get("number_of_pages_median")),
    )


def search(query):
    """Search Open Library and return cleaned results.

    Raises OpenLibraryError with a friendly message if anything goes wrong.
    """
    try:
        response = requests.get(
            SEARCH_URL,
            params={"q": query, "fields": FIELDS, "limit": RESULT_LIMIT},
            headers={"User-Agent": build_user_agent()},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    # Timeout before ConnectionError: a connect timeout is both, and the
    # timeout message is the more accurate one.
    except requests.Timeout as error:
        raise OpenLibraryError(
            f"Open Library took too long to respond (over {TIMEOUT_SECONDS} "
            "seconds). Try again in a moment."
        ) from error
    except requests.ConnectionError as error:
        raise OpenLibraryError(
            "Could not connect to Open Library. Check your internet connection "
            "and try again."
        ) from error
    except requests.HTTPError as error:
        raise OpenLibraryError(
            describe_http_error(error.response.status_code)
        ) from error
    except requests.JSONDecodeError as error:
        raise OpenLibraryError(UNREADABLE_MESSAGE) from error
    except requests.RequestException as error:
        raise OpenLibraryError(
            "Something went wrong while searching Open Library. Try again later."
        ) from error

    if not isinstance(data, dict) or not isinstance(data.get("docs"), list):
        raise OpenLibraryError(UNREADABLE_MESSAGE)

    results = [r for r in map(_clean, data["docs"]) if r is not None]
    total = data.get("numFound")
    if not isinstance(total, int):
        total = len(results)
    return SearchResults(total=total, results=results)
