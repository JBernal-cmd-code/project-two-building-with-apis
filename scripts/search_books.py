"""Search Open Library for books from the command line.

This script proves the app can get book data from the Open Library Search API
(https://openlibrary.org/dev/docs/api/search) and handle the cases where a
search finds nothing or the request fails.

Run it with:  uv run scripts/search_books.py
"""

import os
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

SEARCH_URL = "https://openlibrary.org/search.json"
APP_NAME = "BookShelfScript/1.0"
TIMEOUT_SECONDS = 10
RESULT_LIMIT = 10
# Ask Open Library for only the fields we display, so responses stay small.
FIELDS = "key,title,author_name,first_publish_year"
QUIT_WORDS = {"", "q"}
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

MISSING_EMAIL_WARNING = """\
Warning: CONTACT_EMAIL is not set.
  Open Library asks apps to include a contact email in their User-Agent header.
  To add yours:
    1. Copy .env.example to .env in the project folder.
    2. Replace you@example.com with your email address.
  Searching will still work without it.
"""


class SearchError(Exception):
    """A failed search. The message is written to be shown to the user."""


@dataclass
class SearchResults:
    """The useful parts of an Open Library search response."""

    total: int
    books: list[dict]


def build_user_agent(email: str) -> str:
    """Return the User-Agent header value, including the email when we have one."""
    if email:
        return f"{APP_NAME} ({email})"
    return APP_NAME


def describe_http_error(status_code: int) -> str:
    """Turn an HTTP error status code into a message for the user."""
    if status_code in (403, 429):
        return (
            f"Open Library says we are sending too many requests "
            f"(HTTP {status_code}). Wait a few seconds and try again."
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


def search_books(query: str, user_agent: str) -> SearchResults:
    """Search Open Library and return the results.

    Raises SearchError with a friendly message if the request fails.
    """
    try:
        response = requests.get(
            SEARCH_URL,
            params={"q": query, "fields": FIELDS, "limit": RESULT_LIMIT},
            headers={"User-Agent": user_agent},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    # Timeout is checked before ConnectionError because a connect timeout
    # counts as both, and the timeout message is the more accurate one.
    except requests.Timeout as error:
        raise SearchError(
            f"Open Library took too long to respond (over {TIMEOUT_SECONDS} "
            "seconds). Try again in a moment."
        ) from error
    except requests.ConnectionError as error:
        raise SearchError(
            "Could not connect to Open Library. Check your internet connection "
            "and try again."
        ) from error
    except requests.HTTPError as error:
        raise SearchError(describe_http_error(error.response.status_code)) from error
    except requests.JSONDecodeError as error:
        raise SearchError(
            "Open Library sent back a response we could not read. Try again later."
        ) from error
    except requests.RequestException as error:
        raise SearchError(
            "Something went wrong while searching Open Library. Try again later."
        ) from error

    if not isinstance(data, dict) or not isinstance(data.get("docs"), list):
        raise SearchError(
            "Open Library sent back a response we could not read. Try again later."
        )

    books = data["docs"]
    return SearchResults(total=data.get("numFound", len(books)), books=books)


def format_book(number: int, book: dict) -> str:
    """Format one search result as a numbered, multi-line block of text."""
    title = book.get("title") or "Untitled"
    authors = ", ".join(book.get("author_name") or []) or "Unknown author"
    year = book.get("first_publish_year") or "unknown year"
    key = book.get("key") or "unknown"
    # Line the detail rows up under the title, even for two-digit numbers.
    indent = " " * len(f"{number}. ")
    return (
        f"{number}. {title}\n"
        f"{indent}by {authors} | first published {year}\n"
        f"{indent}Open Library ID: {key}"
    )


def format_results(query: str, results: SearchResults) -> str:
    """Format a whole search: a header line followed by each book."""
    if not results.books:
        return (
            f'No books matched "{query}". Check the spelling or try fewer '
            "or different words."
        )

    noun = "result" if results.total == 1 else "results"
    header = (
        f'Found {results.total:,} {noun} for "{query}" (showing {len(results.books)}):'
    )
    blocks = [format_book(number, book) for number, book in enumerate(results.books, 1)]
    return header + "\n\n" + "\n\n".join(blocks)


def main() -> None:
    """Ask for searches in a loop until the user quits."""
    load_dotenv(ENV_FILE)
    email = os.getenv("CONTACT_EMAIL", "").strip()
    if not email:
        print(MISSING_EMAIL_WARNING)
    user_agent = build_user_agent(email)

    print("Open Library book search")
    while True:
        try:
            query = input("\nSearch for a book (press Enter or type q to quit): ")
        except EOFError:
            break
        query = query.strip()
        if query.lower() in QUIT_WORDS:
            break

        try:
            results = search_books(query, user_agent)
        except SearchError as error:
            print(f"\n{error}")
            continue
        print()
        print(format_results(query, results))

    print("Goodbye!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
