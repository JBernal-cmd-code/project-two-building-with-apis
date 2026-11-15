# PRD: MyChapterCollection

**Status:** Approved design, ready for planning
**Date:** 2026-11-14
**Source:** Design interview (grill-me session), the external API research document, the existing Open Library search script, and the My Collection layout prototype.

## Problem Statement

Readers lose track of their books. The books they want to read, the one they're halfway through, and the ones they finished and loved end up in different places: notes apps, screenshots, memory. General book sites are built around public reviews and social feeds, not a private record of "where am I in this book and what did I think of it." Readers need one private place to find a book, keep it, and record their own progress, rating, and thoughts. They also need that record to stay available whether or not the outside book service is working.

## Solution

MyChapterCollection is a personal reading tracker built with Django.

- **Finding books:** a signed-in reader searches the Open Library catalog and saves the books they want to their own collection with one click. They never leave their search results.
- **Saved data is local:** each saved book's details are copied into the app's own database. The collection keeps working, with search, filters, sorting, and pagination, even if Open Library is down.
- **Tracking:** for each book, the reader records a reading status, current page, total pages, a 1–5 star rating, and private notes. A progress bar shows how far along they are.
- **Privacy:** every collection is private to its owner.
- **API:** the app has its own authenticated REST API for listing, creating, updating, and deleting saved books, with the same privacy rules as the website.
- **Clear errors:** when Open Library is slow or unavailable, the reader gets a clear, friendly message and a reminder that their saved books are still available.

## User Stories

### Accounts and access

1. As a visitor, I want a public home page that explains what the app does, so that I can decide whether to sign up.
2. As a visitor, I want to create an account with a username and password, so that I can start my own private collection.
3. As a new user, I want to be logged in right after signing up, so that I can start using the app without another step.
4. As a returning user, I want to log in and log out, so that my collection is only available to me.
5. As a logged-out visitor, I want to be sent to the login page when I open a protected page, and then returned to that page after I log in, so that I don't lose my place.
6. As a user, I want other users to be unable to see, edit, or delete my books, whether they guess a web address or call the API, so that my collection stays private.
7. As a user, I want another user's book to look like it doesn't exist (not found) rather than "forbidden," so that nobody can learn what's in my collection by probing IDs.

### Searching Open Library

8. As a user, I want to search Open Library by title or author from a search page, so that I can find books to add to my collection.
9. As a user, I want to see the top 20 matching results with cover, title, author, and first publish year, so that I can recognize the right book quickly.
10. As a user, I want to see how many total matches there were and a tip to refine my search, so that I know what to do if my book isn't in the top results.
11. As a user, I want a clear message when my search finds nothing, so that I know to check spelling or try different words.
12. As a user, I want to click Save on a result and have only that result's button change to an "In your collection" badge, without the page reloading or my results clearing, so that I can save several books from one search.
13. As a user, I want results I already own to show an "In your collection" badge that links to my saved book, instead of a Save button, so that I don't save duplicates and can jump straight to my copy.
14. As a user, I want saving to work even if Open Library goes down right after my search, so that a brief outage doesn't cost me the books I picked.
15. As a user, I want saving to still work when JavaScript is off, returning me to the same search, so that the app works in any browser.

### Error handling (Open Library problems)

16. As a user, I want a friendly message when Open Library takes too long (more than 5 seconds), so that I'm not left staring at a page that seems frozen.
17. As a user, I want a friendly message when the app can't connect to Open Library, so that I understand the problem isn't my collection.
18. As a user, I want a specific "too many requests, wait a moment" message when Open Library rate-limits the app, so that I know waiting will fix it.
19. As a user, I want a "having problems right now" message when Open Library has a server error, so that I know to try again later.
20. As a user, I want a friendly message when Open Library sends back something unreadable, so that the app never shows a crash page.
21. As a user, I want my search text to stay in the box after an error, and a link reminding me my saved books are still available, so that I can retry or go to my collection easily.

### My Collection (browsing saved books)

22. As a user, I want My Collection to show my saved books as a grid of covers (about 5 per row on a wide screen), each with title, author, status badge, rating, and progress bar, so that it feels like a real reading app.
23. As a user, I want a placeholder that looks like a plain book cover (with the title) when a book has no cover or its image fails to load, so that the page never shows broken images.
24. As a user, I want the rating space left empty on cards for unrated books, so that cards look clean.
25. As a user, I want the progress bar hidden for Want to read books and for books at page 0, so that cards only show progress when there is some.
26. As a user, I want each status badge to have its own color, so that I can scan my collection by status at a glance.
27. As a user, I want a search box in the sidebar that matches title or author (case-insensitive), so that I can find a book in my collection quickly.
28. As a user, I want a status filter in the sidebar showing a count next to each status, so that I can see how many books are in each state and filter by one.
29. As a user, I want the status counts to reflect my current search and rating filter, so that the numbers match what I'd see if I clicked them.
30. As a user, I want a minimum rating filter (any, or 1★ and up through 5★ only), so that I can find my favorite books.
31. As a user, I want a reset filters link, so that I can return to my full collection in one click.
32. As a user, I want a sort dropdown at the top right with six options (recently added, recently updated, title A–Z, author A–Z, rating high to low, publish year newest first), so that I can order my books the way I need.
33. As a user, I want unrated books sorted last when sorting by rating, and books without a year sorted last when sorting by year, so that sorted lists put meaningful values first.
34. As a user, I want filters, search, and sort to combine, so that I can ask things like "Reading, 4★ and up, by Tolkien, sorted by title."
35. As a user, I want my collection paginated at 20 books per page, so that large collections stay fast and readable.
36. As a user, I want moving to the next or previous page to keep my search, filters, and sort, so that paging doesn't undo my choices.
37. As a user, I want any change to search or filters to send me back to page 1, so that I never land on an empty page that no longer exists.
38. As a user, I want filter, sort, and page changes to update the collection without a full page reload, so that browsing feels smooth.
39. As a user, I want the address bar to reflect my current search, filters, sort, and page, so that Back, refresh, and bookmarks all work.
40. As a user, I want an out-of-range or invalid page number in the URL to show a sensible page instead of an error, so that edited or old links don't break.
41. As a user, I want unknown filter or sort values in the URL to fall back to defaults, so that the page can't be broken by editing the URL.
42. As a user, I want a friendly empty state with a clear-filters button when nothing matches, so that I know what to do next.
43. As a user, I want My Collection to work completely when Open Library is down, so that my reading record is always available.

### Book detail, editing, and removing

44. As a user, I want to click a book in my collection to open its own detail page, so that I can see everything about it and update it.
45. As a user, I want the detail page to show a larger cover, title, authors, and first publish year, so that I can confirm which book I'm editing.
46. As a user, I want to set the reading status to Want to read, Reading, Finished, or Did not finish, so that my collection reflects what I'm actually doing.
47. As a user, I want newly saved books to start as Want to read, so that I don't have to set it for every save.
48. As a user, I want to record my current page and correct the total page count, so that my progress is accurate for my edition.
49. As a user, I want the total page count prefilled from Open Library when it's available, so that I usually don't have to type it.
50. As a user, I want to be stopped from entering a current page higher than the total pages, so that typos don't create impossible progress.
51. As a user, I want marking a book Finished to set my current page to the total page count (when it's known), so that finished books always show 100%.
52. As a user, I want to give a book a whole-star rating from 1 to 5, or leave it unrated, so that I can remember how much I liked it.
53. As a user, I want to write private notes on a book, displayed as plain text, so that I can keep my thoughts with the book.
54. As a user, I want to see a "Saved" confirmation after editing, and clear errors next to any invalid field, so that I know whether my changes went through.
55. As a user, I want book facts from Open Library (title, authors, year, cover, work ID) to be fixed after saving, so that my notes and rating always stay attached to the right book.
56. As a user, I want a Remove button that opens a confirmation dialog warning that my status, rating, and notes will also be deleted, so that I don't delete a book by accident.
57. As a user, I want to return to My Collection with a "Removed '<title>' from your collection" message after deleting, so that I know it worked.

### REST API

58. As an API client, I want to get a token by posting my username and password, so that I can call the API from tools like curl or Postman.
59. As an API client, I want to authenticate with either my browser session or a token, so that the browsable API works in the browser and scripts work outside it.
60. As an API client, I want unauthenticated requests rejected with 401, so that it's clear login is required.
61. As an API client, I want to list my saved books with the same search, status, minimum rating, sort, and page parameters as the website, paginated 20 per page with count, next, and previous links, so that I can browse my collection from code.
62. As an API client, I want to create a saved book by sending its Open Library work key, title, and optional authors, year, cover ID, and total pages, so that I can add books without the website.
63. As an API client, I want work keys accepted with or without the "/works/" prefix and invalid keys rejected with a clear error, so that I can paste keys straight from Open Library.
64. As an API client, I want a missing or blank title rejected with a clear error, so that I can't create unnamed books.
65. As an API client, I want a duplicate save rejected with 400 and "This book is already in your collection.", so that I can tell "created" from "already there."
66. As an API client, I want to retrieve, update (full or partial), and delete one of my saved books, so that I can manage my collection from code.
67. As an API client, I want book facts to be read-only on update, with any changes to them ignored, so that the API matches the website's rules.
68. As an API client, I want the same validation rules as the website (rating range, page limits, Finished auto-fill), so that data is consistent no matter how it was entered.
69. As an API client, I want another user's book to return 404 for every method, so that the API can't be used to probe other collections.
70. As an API client, I want creating and editing books through the API to never depend on Open Library, so that the API keeps working during an outage.

### Demo data and developer experience

71. As a grader or developer, I want one command that creates a demo user and about 25 realistic saved books, so that I can see search, filters, sort, and pagination right away.
72. As a grader or developer, I want the demo books to use real Open Library work keys and cover IDs, with a few books deliberately missing a cover, so that real covers and the placeholder both show.
73. As a grader or developer, I want the demo command to work offline and to be safe to run twice without duplicating books, so that I can reset or reseed with confidence.
74. As a grader, I want the original command-line search script to keep working on its own, with its existing tests still passing, so that earlier graded work is unchanged.
75. As a developer, I want the whole test suite to run offline and fail loudly if any test tries to reach the real network, so that tests are fast and reliable.

## Implementation Decisions

### Project structure

- A Django project at the repo root, managed with uv. The settings package is named `config` to avoid a nested folder with the same name as the project.
- Two apps:
  - **books:** the saved book model, forms, website views, API serializers and viewsets, the Open Library client, and the demo seed command.
  - **accounts:** sign-up plus the login and sign-up templates.
- Shared templates (base layout with navbar, theme, and flash messages; the public home page) live in a project-level templates directory.
- All tests live in the existing top-level tests folder, split by area (models, views, API, Open Library client, seed command), next to the existing script tests. Pytest settings in the project config gain pytest-django and the Django settings module.
- SQLite database.

### Data model: a single `SavedBook` table

One row per user per saved book. Book facts are copied onto the row, with no shared catalog table.

| Field | Kind | Rules |
|---|---|---|
| owner | link to user | required; always set by the server from the logged-in user, never from input |
| ol_work_key | short text | required; stored in short form (e.g. `OL27482W`); a leading `/works/` is stripped; must match `OL` + digits + `W` |
| title | text | required; blank or whitespace-only rejected |
| authors | text | optional; multiple names joined with ", "; displayed as "Unknown author" when empty |
| first_publish_year | whole number | optional |
| cover_id | whole number | optional; cover image URL built from it at display time (medium size by ID, which avoids the covers rate limit) |
| total_pages | whole number | optional; 1 or more; prefilled from Open Library's median page count when available |
| status | choice | `want_to_read` (default), `reading`, `finished`, `abandoned`; labels "Want to read", "Reading", "Finished", "Did not finish" |
| current_page | whole number | 0 or more; default 0; cannot exceed total_pages when total_pages is set |
| rating | whole number | optional; 1–5; empty means unrated |
| notes | long text | optional; no length limit; rendered as escaped plain text |
| created_at / updated_at | timestamps | automatic |

- Unique constraint on owner plus work key.
- The work key format rule is one shared validator on the model, used by both the website form and the API.
- Cross-field rule: current page must not exceed total pages when total pages is set.
- Finished auto-fill: when status is Finished and total pages is set, current page is set to total pages on save. This lives in the model, so the website and API behave the same. Nothing changes when total pages is empty. There are no other status-driven rules: ratings and pages are allowed in any status.
- No description, subjects, or raw API response is stored.

### Mutability rule (website and API)

- Set at creation and read-only afterward: work key, title, authors, first publish year, cover ID.
- Editable after creation: status, current page, total pages, rating, notes.
- The edit form only shows the editable fields. The API serializer treats the locked fields as writable on create and read-only on update, so changes to them in an update are ignored.

### Access control

- Public pages: home, login, sign-up. Everything else requires login. Logged-out website visitors are redirected to login with a return-to parameter.
- Ownership is enforced by starting every website and API query from "the current user's saved books." Another user's book returns 404 on every page and every API method. There are no separate per-object permission checks.

### Accounts

- Django's built-in login and logout views and the built-in user creation form (username and password twice) for sign-up. New users are logged in right after signing up.
- No email verification, password reset by email, or social login.

### Open Library client (in the books app)

- A new app-side client module modeled on the existing script's design, adapted for the app: search endpoint, 20 results, fields including work key, title, author names, first publish year, cover ID, and median page count; 5-second timeout; a User-Agent naming the app plus the contact email from the environment when set.
- A single attempt per search. No retries and no caching of search responses.
- Failures raise a friendly-message error, mapped the same way as the script: timeout, connection error, 403/429 (rate limited), 5xx (provider trouble), other HTTP errors, unreadable or wrongly shaped JSON, other request errors.
- Returns cleaned, display-ready results (authors joined, missing fields handled).
- The command-line script and its tests are not modified. The small amount of repeated error-handling code is an accepted trade-off.

### Search page

- Login required. A query box; results shown as cards in the same visual style as the collection.
- Shows the top 20 results, the total match count, and a tip to refine the search. No paging of Open Library results.
- A "no matches" message when nothing is found.
- On a client error, a warning alert above the results area with the friendly message, the query kept in the box, and a link to My Collection noting saved books are still available.
- One lookup per search to find which result work keys the current user already owns. Those results show an "In your collection" badge linking to the saved book in place of Save.
- **Save interaction:** each result's Save button is a small form posting the book facts (work key, title, joined authors, year, cover ID, median page count) as hidden fields.
  - With HTMX, the POST targets only that button and the server responds with a badge partial that replaces it. The rest of the page is untouched.
  - A duplicate save also responds with the badge. Other validation failures respond with a small inline error for that card only.
  - Without JavaScript, the same POST redirects back to the same search URL.
- Saving never calls Open Library.

### My Collection page

- Layout from the chosen prototype (Variant D): left sidebar with search box, status filter (All plus four statuses, each with a count), minimum rating filter (Any, 1★ and up … 5★ only), and a reset filters link; sort dropdown at the top right; cover grid of about 5 per row on wide screens (fewer on narrow ones).
- Card contents: cover or placeholder, title, author, colored status badge, stars (nothing when unrated), progress bar with percentage (only when total pages is known, progress is above 0, and status is not Want to read).
- Query parameters, shared with the API: `q` (title or authors, case-insensitive contains), `status`, `min_rating`, `ordering` (`-created_at` default, `-updated_at`, `title`, `authors`, `-rating`, `-first_publish_year`), `page`.
- Rating sort puts unrated books last; year sort puts unknown years last; ties break by title.
- Status counts are computed with the search and rating filters applied but not the status filter.
- Unknown filter or sort values fall back to defaults. Out-of-range pages show the last page, and invalid page values show page 1 (Django's safe page lookup).
- 20 books per page. Pagination links are built from the current query string with only the page changed. The filter form carries no page field, so any filter or search submit returns to page 1.
- **HTMX interaction:** the sidebar and grid are one GET form. Changing a status, rating, or sort, pressing Enter in search, or clicking a pagination link issues an HTMX GET that replaces the whole collection area (counts, grid, pagination) and pushes the new URL to the address bar. The view returns the full page normally and only the collection partial when the request comes from HTMX. Without JavaScript it is an ordinary GET form.
- Friendly empty state with a clear-filters action.
- Uses only local data. Never calls Open Library.

### Cover display (search, collection, detail)

- No cover ID: render the placeholder directly.
- Cover ID present: render the Open Library cover image. If it fails to load, a small inline error handler swaps in the placeholder.
- Placeholder: a soft, tinted "plain book" with spine shading, a small book icon, the title, and a small "No cover" label (icon only at small sizes). Not a large empty gray box.

### Book detail page

- Login required, owner only (404 otherwise).
- Shows a larger cover, title, authors, first publish year, status, rating, and progress, plus the edit form (status, current page, total pages, rating, notes).
- Saving is a normal form POST using Post/Redirect/Get. Success reloads the page with a "Saved" flash message. Invalid input re-renders the form with field-level errors. No HTMX on this page.
- **Remove:** a Remove button opens a DaisyUI modal (native dialog element, opened by a one-line inline call) warning that status, rating, and notes will be deleted. The modal's confirm button is a POST form to a dedicated delete URL. The delete view accepts POST only. After deletion the user is redirected to My Collection with a "Removed '<title>' from your collection." message.

### REST API (Django REST Framework)

- One model viewset for saved books: list, create, retrieve, full update, partial update, delete.
- Authentication: session and token (DRF's built-in token auth, with its app and migration). A token endpoint accepts username and password and returns the user's token. Tokens do not expire.
- Permission: authenticated users only. Unauthenticated requests receive 401.
- Queryset always limited to the current user's books, so other users' books return 404.
- Owner is set by the server on create and never accepted from input.
- Validation is shared with the model: work key format (prefix stripped), required non-blank title, rating range, page rules, Finished auto-fill.
- Duplicate create returns 400 with "This book is already in your collection." The uniqueness check must account for the owner being server-set.
- List supports the same `q`, `status`, `min_rating`, `ordering`, `page` parameters as the website with the same fallbacks; page number pagination at 20 per page with count, next, previous, and results.
- The browsable API stays enabled for logged-in browser sessions.

### Styling and front-end assets

- Tailwind CSS with DaisyUI, built through `django-tailwind-cli` using the standalone Tailwind executable. No Node.js or npm. The exact setting that enables DaisyUI with this package must be confirmed in its documentation during setup.
- A custom DaisyUI theme based on the light theme with warm off-white base colors (page background, lighter cream for cards and navbar, warm border tone), as in the prototype.
- Status colors: Want to read uses secondary, Reading uses info, Finished uses success, Did not finish uses warning. Soft badges with a matching colored dot.
- HTMX is served as a pinned, locally stored static file, not from a CDN.
- Shared shell: a navbar with the app name, "Find books" and "My Collection" links, and the user menu with log out. Flash messages are rendered in the base layout.

### Demo data command

- A management command that creates (or reuses) a `demo` user, prints its password to the terminal, and creates about 25 saved books across all four statuses, a mix of rated and unrated, with and without total pages, plus notes on some.
- Book data is written into the command and never fetched at run time, so it works offline.
- Work keys, cover IDs, and page counts must be real values, looked up once from the Open Library search API while building the command. Each cover must be checked to load (using the covers endpoint's option that returns 404 for missing images). About 4 books deliberately have no cover ID so the placeholder appears.
- Running it twice skips books the demo user already has.
- The demo password is for local use only, and the README says so.

## Testing Decisions

### What makes a good test here

- Tests check behavior a user or API client can see: status codes, redirects, rendered content, response JSON, and database rows. They do not check internal function calls or template structure.
- Each rule from the design gets at least one focused test. Combinations are covered by one combined test rather than every pairing.
- Tests never depend on Open Library being reachable.

### Tools and patterns

- pytest with pytest-django, plus Django's test client and DRF's API client.
- Open Library calls are faked by replacing the HTTP get function with pytest's monkeypatch, the same technique the existing script tests use. Fake responses are small hand-written dictionaries, and errors are raised directly.
- An autouse fixture in the shared test configuration makes any network call that wasn't faked fail loudly.
- Prior art: the existing script test suite (28 tests, all passing) shows the fake-response helpers, network and HTTP error cases, and unreadable-response cases to mirror for the app client.

### Modules and behaviors to test

- **SavedBook model and validation:**
  - work key format, with and without the prefix, plus invalid keys
  - required, non-blank title
  - rating bounds and empty rating
  - current page not above total pages
  - Finished auto-fill, with and without total pages
  - unique owner plus work key
  - default status
- **Open Library client:** sends the expected query, fields, limit, timeout, and User-Agent. Also covers result cleanup (missing authors, year, cover, or pages), no-match results, and each failure type mapping to its friendly message.
- **Search page:**
  - login required
  - results rendered
  - total and tip shown
  - no-match message
  - each error shows the alert, keeps the query, and shows the collection link
  - owned results show the badge instead of Save
- **Save from search:**
  - an HTMX save returns the badge partial and creates exactly one row
  - a duplicate save returns the badge and creates no new row
  - invalid data returns the inline error
  - a non-HTMX save redirects back to the search
  - saving makes no Open Library call
- **My Collection:**
  - login required
  - only the owner's books appear
  - each filter and sort on its own, including the null-last ordering
  - one combined filter test
  - status counts respect the search and rating filters
  - pagination keeps parameters
  - a filter change returns page 1
  - out-of-range and invalid pages
  - unknown values fall back to defaults
  - the full page versus the HTMX partial response
  - the empty state
- **Detail, edit, and delete:**
  - owner sees the page; another user gets 404 on view, edit, and delete
  - a valid edit redirects with the "Saved" message and persists
  - an invalid edit shows field errors and does not persist
  - locked fields can't be changed through the form
  - a GET to the delete URL does not delete
  - a POST deletes, redirects, and shows the removed message
- **Accounts:**
  - sign-up creates a user and logs them in
  - login and logout work
  - protected pages redirect to login with a return-to parameter
- **API:**
  - getting a token; a token request works; a bad token is rejected
  - unauthenticated requests return 401
  - list is limited to the owner and is paginated
  - list filters and ordering use the website's parameters
  - create succeeds and sets the owner from the request; owner in the input is ignored
  - create rejects bad work keys and missing titles
  - duplicate create returns 400 with the message
  - retrieve and partial update work; updates ignore locked fields; validation rules apply
  - delete works
  - every method on another user's book returns 404
- **Demo command:** creates the user and books; running it twice doesn't duplicate books.
- **Existing script:** its tests must keep passing unchanged. The full suite is run after every build phase to confirm this.

## Out of Scope

- Paging, "load more," or caching of Open Library search results.
- Automatic retries of failed Open Library requests.
- Fetching extra book details from Open Library (descriptions, subjects, editions, author pages), and any call to Open Library when saving.
- A shared book catalog, author records, or any cross-user features (popularity, "others are reading this," public profiles, reviews, social feeds).
- Editing book facts after saving, or refreshing saved book data from Open Library.
- Reading dates (started on, finished on), reading history, statistics, goals, or an "on hold" status.
- Half-star ratings.
- Searching inside notes, sorting by progress percentage, a selectable page size, or a year-range filter.
- A side panel or inline HTMX editing on the collection or detail pages, and live search-as-you-type.
- Email verification, password reset by email, social login, and JWT or expiring tokens.
- Caching or self-hosting cover images.
- Deployment and production hosting configuration.
- Changes to the existing command-line search script or its tests.

## Further Notes

- **Requirements map:**
  - req 1 (one clear purpose): a private reading tracker
  - req 2 (find books through Open Library): the search page
  - req 3 (still works when Open Library is down): book facts are copied locally; collection, detail, editing, and the API never call Open Library
  - req 4 (user's own info): status, current page, total pages, rating, notes
  - req 5 (search, filter, sort, paginate saved books): the collection page and the API list
  - req 6 (access enforced on website and API): login required plus owner-scoped queries on both
  - req 7 (the app's own API): the DRF viewset
  - req 8 (helpful message when Open Library fails): client error mapping shown on the search page
- **Open Library usage rules:** identify the app with a User-Agent and contact email; stay under 1 request per second unidentified or 3 identified; make requests on behalf of real users only; no bulk downloads. One request per search and none on save keeps the app well within these limits. Requesting covers by cover ID avoids the covers endpoint's per-IP rate limit.
- **Open Library schema:** its search schema is documented as not guaranteed to be stable, which is another reason to copy only the needed fields into the local model.
- **Prototype:** the chosen collection layout and its decision record are in the prototypes folder (Variant D). Treat it as the visual reference for the collection page, the cover placeholder, the badges, and the theme.
- **Suggested next step:** break this PRD into tracer-bullet build phases, each ending with the full test suite, including the script's existing tests, passing.
