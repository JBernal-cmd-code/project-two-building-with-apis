# project-two-building-with-apis

A book tracker built on the [Open Library API](https://openlibrary.org/developers/api).
See [docs/research/external-api-options.md](docs/research/external-api-options.md)
for why Open Library was chosen.

## Setup

Requires [uv](https://docs.astral.sh/uv/). uv installs Python 3.14 and all
packages for you.

```bash
uv sync
cp .env.example .env    # then put your email in .env
```

`CONTACT_EMAIL` in `.env` is sent in the `User-Agent` header, as Open Library
asks. It is optional: without it the script prints a warning and still works.
`.env` is ignored by git.

## Running the web app (MyChapterCollection)

```bash
uv run python manage.py migrate
uv run python manage.py tailwind build   # first run downloads the Tailwind binary
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. Use `uv run python manage.py tailwind runserver`
instead to rebuild the CSS automatically while editing templates.

Styling is Tailwind CSS + DaisyUI through `django-tailwind-cli`. With
`TAILWIND_CLI_USE_DAISY_UI = True` it downloads the standalone
`tailwindcss-extra` binary (DaisyUI bundled) into `.django_tailwind_cli/`, so no
Node.js or npm is needed. The theme lives in `styles/source.css`; the built
`static/css/tailwind.css` is committed so the app is styled right after cloning.
HTMX is a pinned local file at `static/js/htmx.min.js` (v2.0.4).

`DJANGO_SECRET_KEY` can be set in `.env`; a development-only key is used otherwise.

## Scripts

### `scripts/search_books.py`: search Open Library from the console

```bash
uv run scripts/search_books.py
```

Type a search (title, author, or anything) to see the first 10 matches. Press
Enter on an empty line or type `q` to quit. Ctrl+C also exits.

Every request uses a 10-second timeout. If nothing matches, or if the request
fails (timeout, no connection, an HTTP error such as 503 or 429, or an
unreadable response), the script prints a short message and asks for the next
search instead of crashing.

## Tests and code quality

```bash
uv run pytest            # offline tests, no network calls
uv run ruff check .      # lint
uv run ruff format .     # format
```

The tests replace `requests.get` with fakes, so they check the no-results and
failure messages without touching the network. An autouse fixture in
`tests/conftest.py` blocks sockets, so any test that forgets to fake a request
fails with "Network access is blocked in tests".

### Manual checklist for `search_books.py`

| Step | Expected |
|---|---|
| Run with no `.env` file | Warning explains how to create `.env`, then searching works |
| Search `the hobbit` | "Found N results" header and a numbered list of 10 books |
| Search `zzqxvwplm` | "No books matched" message, then the prompt again |
| Turn off Wi-Fi, search anything | "Could not connect to Open Library" message, then the prompt again |
| Turn Wi-Fi back on, search again | Results appear (the script recovered) |
| Press Enter on an empty line, or type `q` | "Goodbye!" and the script exits |
