# Plan: MyChapterCollection

> Source PRD: `prd/mychaptercollection.md` (approved 2026-11-14)

## Architectural decisions

Durable decisions that apply across all phases:

- **Project layout**: Django project at the repo root, managed with uv. The settings package is `config`. SQLite database. Shared templates (base layout, home page) live in a project-level templates directory.
- **Owning apps**:
  - `books`: the `SavedBook` model, forms, website views, API serializers and viewset, the Open Library client, and the demo seed command.
  - `accounts`: sign-up, plus the login and sign-up templates.
- **URLs** (app-namespaced, `pk`s not slugs):
  - `/`: public home page
  - `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/` (namespace `accounts:`)
  - `/books/`: My Collection (namespace `books:`)
  - `/books/search/`: Open Library search page
  - `/books/save/`: save from search (POST)
  - `/books/<pk>/`: book detail and edit
  - `/books/<pk>/delete/`: remove a book (POST only)
  - `/api/books/`, `/api/books/<pk>/`: DRF router for the saved-book viewset
  - `/api/token/`: token endpoint
- **Model**: one `SavedBook` table, one row per user per saved book, with book facts copied onto the row and no shared catalog.
  - Foreign key `owner` to the user, always set by the server.
  - Unique constraint on owner plus `ol_work_key`.
  - The work key is stored in short form (`OL…W`) through one shared validator that strips a leading `/works/`.
  - Status choices: `want_to_read` (default), `reading`, `finished`, `abandoned`.
  - Cross-field rule: current page must not exceed total pages when total pages is set.
  - Finished auto-fill lives in the model's save.
- **Mutability**:
  - Locked after creation: work key, title, authors, first publish year, cover ID.
  - Editable: status, current page, total pages, rating, notes.
- **Auth and access**:
  - Login is required everywhere except home, login, and sign-up. Logged-out visitors are redirected to login with a return-to parameter.
  - Every website and API query starts from the current user's saved books, so another user's book returns 404.
  - The API uses session plus DRF token auth, and unauthenticated requests get 401.
- **Shared collection query params** (website and API): `q`, `status`, `min_rating`, `ordering` (`-created_at` default, `-updated_at`, `title`, `authors`, `-rating`, `-first_publish_year`), and `page`, at 20 per page. Unknown values fall back to defaults.
- **Open Library**: called only from the search page, with one request per search, a 5-second timeout, and an identifying User-Agent. Collection, detail, save, and the API never call it.
- **Front end**:
  - Tailwind plus DaisyUI via `django-tailwind-cli` (no Node).
  - A custom warm light theme, with the Variant D prototype as the visual reference.
  - HTMX served as a pinned local static file.
- **Testing**: pytest plus pytest-django, with all tests in the top-level `tests/` folder.
  - Open Library is faked with monkeypatch.
  - An autouse fixture makes any unfaked network call fail.
  - The existing script tests must keep passing unchanged after every phase.

---

## Phase 1: Project skeleton, accounts, and app shell

**User stories**: 1, 2, 3, 4, 5, 74, 75

### What to build

Stand up the Django project (`config` settings, `books` and `accounts` apps) under uv, with SQLite and the Tailwind/DaisyUI build working. The shared base layout has the navbar (app name, Find books, My Collection, and a user menu with log out), the warm custom theme, and flash messages.

The public home page explains the app. Visitors can sign up with a username and password and are logged in right away. They can also log in and log out. Protected pages redirect to login and return to the original page afterward. In this phase, the My Collection and search links can point at simple login-required placeholder pages.

Configure pytest-django alongside the existing script tests, and add the autouse fixture that blocks real network access.

### Acceptance criteria

- [ ] `uv run python manage.py runserver` serves the home page with the themed navbar
- [ ] Tailwind/DaisyUI CSS builds without Node, using the standalone executable (the DaisyUI setting is confirmed against the package docs)
- [ ] Sign-up creates a user and logs them in
- [ ] Login and logout work
- [ ] Opening a protected page while logged out redirects to login with a return-to parameter, and logging in returns to that page
- [ ] Flash messages render in the base layout
- [ ] A test that tries to reach the real network fails loudly
- [ ] The full test suite passes, including the 28 existing script tests, unchanged

---

## Phase 2: SavedBook model, demo seed, and basic collection grid

**User stories**: 6, 22, 23, 24, 25, 26, 43, 47, 55 (model side), 71, 72, 73

### What to build

Add the `SavedBook` model and migration with every field, default, and rule from the PRD:

- the shared work key validator with prefix stripping
- a required, non-blank title
- rating 1–5 or empty
- current page not above total pages
- Finished auto-fill
- the owner plus work key uniqueness

Add the demo seed management command. It creates or reuses a `demo` user, prints the password, and writes about 25 hard-coded books with real work keys, cover IDs, and page counts. The books cover all four statuses, a mix of rated and unrated, and about 4 without covers. The command works offline and skips books the demo user already has.

Replace the My Collection placeholder with a real login-required page. It shows only the current user's books as a cover grid of about 5 per row on wide screens. Each card shows:

- the cover image, or a placeholder (a tinted plain book with the title) when the cover is missing or fails to load
- title and author ("Unknown author" when empty)
- a colored status badge
- stars, with nothing shown for unrated books
- a progress bar, only when total pages is known, progress is above 0, and the status is not Want to read

No filters or sorting yet; a simple default order is fine.

### Acceptance criteria

- [ ] Model tests cover:
  - work key with and without `/works/`
  - invalid keys
  - blank or whitespace-only title
  - rating bounds and empty rating
  - current page above total pages rejected
  - Finished auto-fill with and without total pages
  - owner plus work key uniqueness
  - default status of Want to read
- [ ] The seed command creates the demo user and books, and running it twice creates no duplicates
- [ ] The seed command makes no network calls
- [ ] My Collection requires login and shows only the owner's books
- [ ] Cards show the placeholder for books without a cover, and a broken cover image swaps to the placeholder
- [ ] Unrated cards show no stars, and the progress bar is hidden for Want to read and page-0 books
- [ ] Each status badge uses its color: Want to read is secondary, Reading is info, Finished is success, Did not finish is warning
- [ ] My Collection makes no Open Library calls
- [ ] The full suite passes, including the script tests

---

## Phase 3: Book detail, edit, and remove

**User stories**: 7, 44, 45, 46, 48, 50, 51, 52, 53, 54, 55, 56, 57

### What to build

Make each card in My Collection link to `/books/<pk>/`. The demo seed from Phase 2 provides books to open, so this phase doesn't depend on search. The page is login-required and owner-only, and returns 404 for anyone else. It shows:

- a larger cover (or the placeholder), title, authors, and first publish year
- the current status, rating, and progress
- an edit form with only the editable fields: status, current page, total pages, rating (1–5 or unrated), and notes

Notes are rendered as escaped plain text. Saving uses Post/Redirect/Get:

- Success reloads the page with a "Saved" flash message.
- Invalid input re-renders the form with field-level errors.
- The model's Finished auto-fill and page rule apply.
- There is no HTMX on this page.

A Remove button opens a DaisyUI modal (native dialog) warning that status, rating, and notes will also be deleted. Its confirm button is a POST form to `/books/<pk>/delete/`. The delete view accepts POST only. After deleting, it redirects to My Collection with "Removed '<title>' from your collection."

### Acceptance criteria

- [ ] Clicking a card in My Collection opens that book's detail page
- [ ] The owner sees the detail page, and another user gets 404 on view, edit, and delete
- [ ] A valid edit redirects with the "Saved" message, and the changes persist
- [ ] An invalid edit (current page above total, rating out of range) shows field errors and does not persist
- [ ] Marking a book Finished with total pages known sets current page to total pages
- [ ] Locked fields (work key, title, authors, year, cover ID) can't be changed by posting them to the form
- [ ] Notes containing HTML are shown escaped
- [ ] A GET to the delete URL does not delete
- [ ] A POST deletes the book, redirects to My Collection, and shows the removed message
- [ ] The full suite passes, including the script tests

---

## Phase 4: Open Library search and save from search

**User stories**: 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 49

### What to build

Add the app-side Open Library client in `books`. It is modeled on the script's design but kept separate from it. It makes one search request with:

- the needed fields: work key, title, author names, first publish year, cover ID, median page count
- a limit of 20
- a 5-second timeout
- a User-Agent naming the app, plus the contact email from the environment when set

It returns cleaned, display-ready results and raises a friendly-message error for each failure type:

- timeout
- connection error
- 403/429 rate limiting
- 5xx errors
- other HTTP errors
- unreadable or wrongly shaped JSON
- other request errors

The login-required search page at `/books/search/` shows:

- a query box, and the top 20 results as cards (cover, title, author, year)
- the total match count and a tip to refine the search
- a message when nothing matches
- on an error, a warning alert with the friendly message, the query kept in the box, and a link to My Collection saying saved books are still available

One query per search finds which result work keys the user already owns. Those results show an "In your collection" badge that links to the saved book's detail page (built in Phase 3).

Each other result has a Save form that posts the book facts as hidden fields to `/books/save/`, including the median page count as total pages:

- With HTMX, only that button is replaced with the badge partial, and the rest of the page stays as it is.
- A duplicate save also returns the badge.
- Other validation failures return a small inline error for that card.
- Without JavaScript, the POST redirects back to the same search URL.
- Saving never calls Open Library.

### Acceptance criteria

- [ ] Client tests check the query, fields, limit, timeout, and User-Agent that are sent
- [ ] Client tests cover result cleanup (missing authors, year, cover, or pages) and no-match results
- [ ] Each failure type maps to its friendly message
- [ ] The search page requires login, renders results, and shows the total and the tip
- [ ] The search page shows the no-match message
- [ ] Each error type shows the alert, keeps the query, and shows the collection link, with no crash page
- [ ] Owned results show the badge instead of Save, and the badge links to that book's `/books/<pk>/` detail page
- [ ] The badge returned after a new save also links to the new book's detail page
- [ ] An HTMX save returns the badge partial and creates exactly one row with status Want to read and total pages prefilled
- [ ] A duplicate save returns the badge and creates no row
- [ ] Invalid save data returns the inline error
- [ ] A non-HTMX save redirects back to the search URL
- [ ] Saving makes no Open Library call (the network-blocking fixture proves this)
- [ ] The full suite passes, including the script tests

---

## Phase 5: Collection search, filters, sort, pagination, and HTMX updates

**User stories**: 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42

### What to build

Turn My Collection into the full Variant D layout. A left sidebar holds:

- a search box (title or authors, case-insensitive contains)
- a status filter (All plus the four statuses, each with a count)
- a minimum rating filter (Any, 1★ and up … 5★ only)
- a reset filters link

The sort dropdown sits at the top right with the six orderings. Rating sort puts unrated books last, year sort puts unknown years last, and ties break by title. Filters, search, and sort combine.

Status counts apply the search and rating filters but not the status filter. Pagination works as follows:

- 20 per page, using Django's safe page lookup: out-of-range shows the last page, invalid shows page 1
- pagination links are built from the current query string with only `page` changed
- the filter form carries no page field, so any filter or search change returns to page 1

Unknown filter or sort values fall back to defaults. A friendly empty state offers a clear-filters action.

The sidebar and grid are one GET form that works without JavaScript. With HTMX, these actions issue an HTMX GET that replaces the whole collection area (counts, grid, pagination) and pushes the new URL:

- changing status, rating, or sort
- pressing Enter in search
- clicking a pagination link

The view returns the full page normally and only the collection partial for HTMX requests. Filtering and ordering logic should be reusable by the API in Phase 6.

### Acceptance criteria

- [ ] Each filter works on its own: `q` matches title or authors case-insensitively, plus `status` and `min_rating`
- [ ] Each of the six orderings works, including unrated last for rating, unknown year last for year, and the title tiebreak
- [ ] One combined test covers status, minimum rating, `q`, and ordering together
- [ ] Status counts reflect the current search and rating filter, but not the status filter
- [ ] Pagination is 20 per page, and next and previous links keep `q`, `status`, `min_rating`, and `ordering`
- [ ] Submitting a filter returns page 1
- [ ] An out-of-range page shows the last page, and a non-numeric page shows page 1
- [ ] Unknown `status`, `min_rating`, and `ordering` values fall back to defaults with no error
- [ ] The empty state shows with a clear-filters action
- [ ] A normal request returns the full page, and an HTMX request returns only the collection partial
- [ ] The HTMX attributes push the URL, so Back, refresh, and bookmarks restore the same view
- [ ] Without JavaScript, the form works as an ordinary GET
- [ ] The full suite passes, including the script tests

---

## Phase 6: REST API

**User stories**: 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70

### What to build

Add Django REST Framework with session and token authentication: the token app and its migration, plus `/api/token/`, which takes a username and password and returns the user's non-expiring token. Only authenticated users are allowed, and unauthenticated requests get 401.

One model viewset at `/api/books/` provides list, create, retrieve, full update, partial update, and delete. The queryset is always the current user's books, so another user's book returns 404 for every method.

List accepts the same `q`, `status`, `min_rating`, `ordering`, and `page` parameters and fallbacks as the website. It uses page-number pagination at 20 per page, with count, next, previous, and results.

The serializer:

- sets the owner from the request and ignores any owner in the input
- accepts work keys with or without `/works/` and rejects invalid ones
- requires a non-blank title
- makes locked fields writable on create and read-only on update, so changes to them are ignored
- applies the model's rating, page, and Finished auto-fill rules

A duplicate create returns 400 with "This book is already in your collection." The uniqueness check must account for the server-set owner. The browsable API stays enabled for logged-in sessions. No API path calls Open Library.

### Acceptance criteria

- [ ] Posting valid credentials to `/api/token/` returns a token
- [ ] A request with that token works
- [ ] A bad token is rejected
- [ ] Unauthenticated requests return 401
- [ ] Session auth works, and the browsable API renders for a logged-in user
- [ ] List returns only the owner's books, paginated with count, next, and previous
- [ ] List filters and ordering use the website's parameters and fallbacks
- [ ] Create succeeds and sets the owner from the request, ignoring any owner in the input
- [ ] Work keys are stored in short form whether or not the input has the `/works/` prefix
- [ ] Create rejects invalid work keys and missing or blank titles with clear errors
- [ ] A duplicate create returns 400 with "This book is already in your collection."
- [ ] Retrieve works
- [ ] Full and partial update work
- [ ] Updates ignore changes to locked fields
- [ ] Rating range, page limit, and Finished auto-fill apply through the API
- [ ] Delete works
- [ ] GET, PUT, PATCH, and DELETE on another user's book each return 404
- [ ] No API test needs Open Library (the network-blocking fixture proves this)
- [ ] The full suite passes, including the script tests
