"""Call MyChapterCollection's own REST API from the command line.

This script talks to the Django app's API (not Open Library). It:

1. Logs in with API_USERNAME and API_PASSWORD from .env to get a token.
2. Lists your saved books, filtered and sorted with query parameters.
3. Updates one field on one book with a PATCH and shows it before and after.

The Django server must be running first:  uv run python manage.py runserver

Run it with:  uv run scripts/my_books_api.py
See all options with:  uv run scripts/my_books_api.py --help
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 10
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

TOKEN_PATH = "/api/token/"
BOOKS_PATH = "/api/books/"

STATUS_LABELS = {
    "want_to_read": "Want to read",
    "reading": "Reading",
    "finished": "Finished",
    "abandoned": "Did not finish",
}
ORDERING_LABELS = {
    "-created_at": "recently added",
    "-updated_at": "recently updated",
    "title": "title (A-Z)",
    "authors": "author (A-Z)",
    "-rating": "highest rated",
    "-first_publish_year": "newest published",
}

# Only the reading-tracking fields can be changed; book facts are locked.
EDITABLE_FIELDS = ("status", "current_page", "total_pages", "rating", "notes")
INTEGER_FIELDS = {"current_page", "total_pages", "rating"}
NULLABLE_FIELDS = {"total_pages", "rating"}
NULL_WORDS = {"", "none", "null"}
DEFAULT_PAGE_STEP = 10
NOTES_PREVIEW_LENGTH = 60

MISSING_CREDENTIALS_MESSAGE = """\
API_USERNAME and API_PASSWORD are not set.
  This script logs in to your own Django app, so it needs an account there.
  To add one:
    1. Copy .env.example to .env in the project folder (if you haven't yet).
    2. Set API_USERNAME and API_PASSWORD to a user of the app. For the demo
       user, run `uv run python manage.py seed_demo` and use the password it
       prints."""


class ApiError(Exception):
    """A failed API call. The message is written to be shown to the user."""

    def __init__(self, message: str, status_code: int | None = None, body=None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


# --- Talking to the API -------------------------------------------------------


class BooksApi:
    """A small client for the app's REST API, authenticated with a token."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(self, method: str, path: str, **kwargs):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        try:
            response = requests.request(
                method,
                self.base_url + path,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
                **kwargs,
            )
        # Timeout is checked before ConnectionError because a connect timeout
        # counts as both, and the timeout message is the more accurate one.
        except requests.Timeout as error:
            raise ApiError(
                f"The Django server at {self.base_url} took too long to respond "
                f"(over {TIMEOUT_SECONDS} seconds)."
            ) from error
        except requests.ConnectionError as error:
            raise ApiError(server_not_running_message(self.base_url)) from error
        except requests.RequestException as error:
            raise ApiError(
                f"Something went wrong while calling {self.base_url}: {error}"
            ) from error

        try:
            body = response.json() if response.content else None
        except requests.JSONDecodeError as error:
            raise ApiError(
                f"{self.base_url}{path} sent back something that isn't JSON "
                f"(HTTP {response.status_code}). Check that API_BASE_URL points "
                "to this Django app."
            ) from error

        if not response.ok:
            raise ApiError(
                describe_http_error(response.status_code, body),
                status_code=response.status_code,
                body=body,
            )
        return body

    def log_in(self, username: str, password: str) -> str:
        """Exchange a username and password for a token, and keep it."""
        try:
            body = self._request(
                "POST", TOKEN_PATH, data={"username": username, "password": password}
            )
        except ApiError as error:
            if error.status_code == 400:
                raise ApiError(
                    f'Login failed for "{username}". Check API_USERNAME and '
                    "API_PASSWORD in .env, and that this user exists in the app."
                ) from error
            raise
        if not isinstance(body, dict) or not body.get("token"):
            raise ApiError("The login response didn't include a token.")
        self.token = body["token"]
        return self.token

    def list_books(self, status: str | None, ordering: str | None) -> dict:
        """Return the first page of the list: ``count`` plus ``results``."""
        params = {"status": status, "ordering": ordering}
        body = self._request(
            "GET", BOOKS_PATH, params={k: v for k, v in params.items() if v}
        )
        if not isinstance(body, dict) or not isinstance(body.get("results"), list):
            raise ApiError("The book list response wasn't in the expected format.")
        return body

    def get_book(self, book_id: int) -> dict:
        try:
            return self._request("GET", f"{BOOKS_PATH}{book_id}/")
        except ApiError as error:
            raise not_found_as_friendly(error, book_id) from error

    def update_book(self, book_id: int, changes: dict) -> dict:
        try:
            return self._request("PATCH", f"{BOOKS_PATH}{book_id}/", json=changes)
        except ApiError as error:
            if error.status_code == 400:
                raise ApiError(
                    "The server rejected the change:\n"
                    + format_validation_errors(error.body)
                ) from error
            raise not_found_as_friendly(error, book_id) from error


def server_not_running_message(base_url: str) -> str:
    return (
        f"Could not connect to the Django server at {base_url}.\n"
        "  Is it running? Start it in another terminal with:\n"
        "    uv run python manage.py runserver\n"
        "  If it runs at a different address, set API_BASE_URL in .env."
    )


def describe_http_error(status_code: int, body) -> str:
    """Turn an HTTP error status code into a message for the user."""
    if status_code in (401, 403):
        detail = body.get("detail") if isinstance(body, dict) else None
        return f"The server refused the request (HTTP {status_code})" + (
            f": {detail}" if detail else "."
        )
    if status_code == 404:
        return "The server couldn't find that (HTTP 404)."
    if status_code >= 500:
        return (
            f"The Django server hit an error (HTTP {status_code}). "
            "Check the runserver terminal for details."
        )
    return f"The server returned an unexpected error (HTTP {status_code})."


def not_found_as_friendly(error: ApiError, book_id: int) -> ApiError:
    if error.status_code == 404:
        return ApiError(f"There's no book with id {book_id} in your collection.")
    return error


def format_validation_errors(body) -> str:
    """Format DRF's error body, like {"rating": ["..."]}, one line per message."""
    if not isinstance(body, dict):
        return f"  {body}"
    lines = []
    for field, messages in body.items():
        if not isinstance(messages, list):
            messages = [messages]
        label = "" if field == "non_field_errors" else f"{field}: "
        lines.extend(f"  {label}{message}" for message in messages)
    return "\n".join(lines)


# --- Choosing the change -----------------------------------------------------


def parse_assignment(text: str) -> tuple[str, object]:
    """Parse ``--set FIELD=VALUE`` into a field name and a JSON-ready value."""
    field, sep, raw = text.partition("=")
    field = field.strip()
    if not sep or field not in EDITABLE_FIELDS:
        raise argparse.ArgumentTypeError(
            f"expected FIELD=VALUE where FIELD is one of {', '.join(EDITABLE_FIELDS)}"
        )
    raw = raw.strip()
    if field in NULLABLE_FIELDS and raw.lower() in NULL_WORDS:
        return field, None
    if field in INTEGER_FIELDS:
        try:
            return field, int(raw)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"{field} must be a whole number, not {raw!r}"
            ) from None
    return field, raw


def default_change(book: dict) -> tuple[str, int]:
    """Move ``current_page`` forward a little, without passing the last page."""
    new_page = (book.get("current_page") or 0) + DEFAULT_PAGE_STEP
    if book.get("total_pages"):
        new_page = min(new_page, book["total_pages"])
    return "current_page", new_page


# --- Formatting --------------------------------------------------------------


def format_progress(book: dict) -> str:
    current = book.get("current_page") or 0
    total = book.get("total_pages")
    if not total:
        return f"page {current} (total unknown)"
    percent = min(100, round(current * 100 / total))
    return f"page {current} of {total} ({percent}%)"


def format_book(book: dict) -> str:
    """Format one saved book as a multi-line block of text."""
    title = book.get("title") or "Untitled"
    authors = book.get("authors") or "Unknown author"
    year = book.get("first_publish_year") or "unknown year"
    status = STATUS_LABELS.get(book.get("status"), book.get("status") or "unknown")
    rating = f"{book['rating']}/5" if book.get("rating") else "not rated"
    lines = [
        f"#{book.get('id')}  {title}",
        f"    by {authors} | first published {year}",
        f"    {status} | {format_progress(book)} | {rating}",
    ]
    notes = (book.get("notes") or "").strip().replace("\n", " ")
    if notes:
        if len(notes) > NOTES_PREVIEW_LENGTH:
            notes = notes[: NOTES_PREVIEW_LENGTH - 3].rstrip() + "..."
        lines.append(f"    Notes: {notes}")
    return "\n".join(lines)


def describe_filters(status: str | None, ordering: str | None) -> str:
    status_text = STATUS_LABELS[status] if status else "any status"
    order_text = ORDERING_LABELS.get(ordering or "-created_at", ordering)
    return f"{status_text}, sorted by {order_text}"


def format_book_list(data: dict, status: str | None, ordering: str | None) -> str:
    """Format the list response: a header line followed by each book."""
    books = data["results"]
    filters = describe_filters(status, ordering)
    if not books:
        return f"No books match those filters ({filters})."
    count = data.get("count", len(books))
    noun = "book" if count == 1 else "books"
    header = f"Found {count} {noun} ({filters})"
    if count > len(books):
        header += f", showing the first {len(books)}"
    return header + ":\n\n" + "\n\n".join(format_book(book) for book in books)


def format_changes(before: dict, after: dict) -> str:
    """List each editable field whose value changed."""
    changed = [
        f"  {field}: {before.get(field)!r} -> {after.get(field)!r}"
        for field in EDITABLE_FIELDS
        if before.get(field) != after.get(field)
    ]
    if not changed:
        return "Nothing changed (the book already had that value)."
    return "Changed:\n" + "\n".join(changed)


# --- Running it --------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List and update your saved books through the MyChapterCollection "
            "REST API. The Django server must be running."
        ),
        epilog=(
            "Examples:\n"
            "  uv run scripts/my_books_api.py\n"
            "  uv run scripts/my_books_api.py --status finished --ordering=-rating\n"
            "  uv run scripts/my_books_api.py --book-id 3 --set status=finished\n"
            "Write orderings that start with '-' as --ordering=-rating."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--status",
        choices=[*STATUS_LABELS, "any"],
        default="reading",
        help="only list books with this status (default: reading)",
    )
    parser.add_argument(
        "--ordering",
        choices=list(ORDERING_LABELS),
        default="title",
        metavar="ORDERING",
        help=f"sort order: {', '.join(ORDERING_LABELS)} (default: title)",
    )
    parser.add_argument(
        "--book-id",
        type=int,
        help="the book to update (default: the first book in the list)",
    )
    parser.add_argument(
        "--set",
        type=parse_assignment,
        metavar="FIELD=VALUE",
        dest="change",
        help=(
            f"the change to make; FIELD is one of {', '.join(EDITABLE_FIELDS)} "
            f"(default: current_page moves forward {DEFAULT_PAGE_STEP} pages)"
        ),
    )
    return parser


def heading(text: str) -> None:
    print(f"\n== {text} ==")


def run(args: argparse.Namespace) -> int:
    base_url = os.getenv("API_BASE_URL", "").strip() or DEFAULT_BASE_URL
    username = os.getenv("API_USERNAME", "").strip()
    password = os.getenv("API_PASSWORD", "")
    if not username or not password:
        print(MISSING_CREDENTIALS_MESSAGE)
        return 1

    api = BooksApi(base_url)
    status = None if args.status == "any" else args.status

    heading(f"1. Logging in to {api.base_url}")
    api.log_in(username, password)
    print(f'Logged in as "{username}". Using the token for the next requests.')

    heading(f"2. Listing books: GET {BOOKS_PATH}")
    data = api.list_books(status, args.ordering)
    print(format_book_list(data, status, args.ordering))

    book_id = args.book_id
    if book_id is None:
        if not data["results"]:
            print(
                "\nNo book to update. Try other filters (for example "
                "--status any), or pick a book with --book-id."
            )
            return 0
        book_id = data["results"][0]["id"]

    heading(f"3. Updating book #{book_id}: PATCH {BOOKS_PATH}{book_id}/")
    before = api.get_book(book_id)
    field, value = args.change or default_change(before)
    print("Before:")
    print(format_book(before))
    print(f"\nSending: {{{field!r}: {value!r}}}")
    after = api.update_book(book_id, {field: value})
    print("\nAfter:")
    print(format_book(after))
    print()
    print(format_changes(before, after))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv(ENV_FILE)
    try:
        return run(args)
    except ApiError as error:
        print(f"\nError: {error}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
