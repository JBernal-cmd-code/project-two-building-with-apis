# External API Options for Project 2

**Sources accessed:** 2026-11-14. All facts come from official provider docs and terms pages, which are linked inline.
**Method:** I read each provider's own docs and terms. For keyless APIs I also fetched the sample request live on 2026-11-14 (marked **"Fetched live"**). For key-based APIs I sent a request without a key so I could record the real error format. "Not verified" means I couldn't find the claim in an official source.

---

## 1. TL;DR

**Top pick: Open Library (books).**
No key, no signup, no credit card, and no approval wait. The [developer page](https://openlibrary.org/developers/api) asks only that frequent callers send a `User-Agent` header with an app name and contact. I fetched the search and work-detail endpoints live and both returned clean JSON with a stable ID (`/works/OL27482W`), title, author, first publish year, and cover ID. On storage, Open Library tells developers to "Cache responses whenever possible." The Internet Archive "does not assert any new copyright or other proprietary rights" over the data ([licensing](https://openlibrary.org/developers/licensing)), so saving picked books locally (req 3) fits the terms. Reading status, rating, pages read, and notes are obvious user fields for req 4.

**Runner-up: TVmaze (TV shows).**
Also no key needed. The data is [licensed CC BY-SA](https://www.tvmaze.com/api) and "can freely be used for any purpose" as long as you credit TVmaze. It has the clearest documented error behavior of any candidate: a stated rate limit ("at least 20 calls every 10 seconds per IP") with an HTTP **429** response, and I confirmed a real JSON **404** body for missing shows. That maps straight onto req 8. Search and detail both worked live. The user fields are a natural watchlist: status (watching, completed, dropped), current season and episode, rating, notes. It ranks second only because TV is a slightly narrower domain than books, and because CC BY-SA's ShareAlike clause is a small extra licensing note to mention.

---

## 2. Comparison table

| Provider | Topic | Key needed / setup time | Free limits | Storage allowed? | Search + detail | Fit: req 2 / 3 / 4 / 8 |
|---|---|---|---|---|---|---|
| **Open Library** | Books | **No key.** User-Agent recommended. Instant | 1 req/s anonymous, 3 req/s identified ([src](https://openlibrary.org/developers/api)) | **Yes.** "Cache responses whenever possible" | `search.json` + `/works/{id}.json` | Strong / Strong / Strong / Good |
| Google Books | Books | Google Cloud API key. Minutes, but needs a Cloud project | Quota numbers not in docs. **Keyless calls returned 429 with quota 0 in my test** | **Restricted.** Google APIs ToS bans keeping cache "longer than permitted by the cache header" and "building databases" | `volumes?q=` + `volumes/{id}` | Good / **Weak** / Strong / Good |
| TheMealDB | Recipes | Test key `1`, no signup. Instant | Rate limit not stated. Some endpoints premium-only | Not addressed. Terms allow you to "copy and modify any content returned from the API" | `search.php?s=` + `lookup.php?i=` | Good / Good / Strong / Fair (200 with `null` on no match) |
| Spoonacular | Recipes | Account + key. No credit card if direct | 50 points/day, 1 req/s. **402** when used up | **Very restricted.** Only id, title, and image URL may be stored indefinitely. Other data max 1 hour | `recipes/complexSearch` + `recipes/{id}/information` | Fair / **Weak** / Strong / Good |
| Edamam | Recipes | Paid plan ($9/mo, 10-day trial) | 10,000 calls/mo, 10/min on lowest plan | Very restricted ("cache only the four basic macro nutrient datapoints") | Not evaluated further | **Fails req 2** |
| RAWG | Games | Account + key. Instant per docs | 20,000 req/month on free plan | Not addressed. ToS bars copying for "publication, distribution or any other commercial purpose" | `games?search=` + `games/{id}` | Strong / Fair (unclear) / Strong / Good |
| IGDB | Games | Twitch account + **2FA** + app registration + OAuth token. About 15–30 min | 4 req/s, 8 open requests, **429** | **Yes, explicitly.** "we prefer if you store and serve the data" | POST `/v4/games` with `search "..."` body | Good / **Strong** / Strong / Good (but more setup) |
| TMDB | Movies/TV | Account + key via account settings. Approval wait not documented | About 40 req/s upper limit, **429** | **Yes, capped:** may not "Cache, for longer than 6 months" | `search/movie` + `movie/{id}` | Strong / Good (6-month cap) / Strong / Good |
| OMDb | Movies | Key emailed. "Email Delays!" warning | 1,000/day free | Not addressed. Content is CC BY-NC 4.0 | `?s=` + `?i=` | Good / Fair / Strong / Good (JSON `Error`) |
| **TVmaze** | TV shows | **No key.** Instant | At least 20 calls / 10 s per IP, **429** | **Yes.** CC BY-SA: "freely be used for any purpose" with credit | `search/shows?q=` + `shows/{id}` | Strong / Strong / Strong / **Strong** |

---

## 3. Per-provider details

### 3.1 Open Library (books): top pick

- **Search endpoint:** `GET https://openlibrary.org/search.json`. Parameters: `q`, `fields` (`*` for all), `sort` (`new`, `old`, `random`, `key`), `lang`, `page`/`limit` or `offset`/`limit`. "Note `page` starts at 1." ([search docs](https://openlibrary.org/dev/docs/api/search))
- **Key search fields:** `key`, `title`, `author_name`, `first_publish_year`, `cover_i`, `edition_count`, `author_key`. The docs warn: "The schema is not guaranteed to be stable" ([search docs](https://openlibrary.org/dev/docs/api/search)). That's a reason to copy fields into your own model.
- **Detail endpoint:** `GET https://openlibrary.org/works/{OLID}.json`. Adding `.json` to a work page "will return a data representation instead of HTML" ([books docs](https://openlibrary.org/dev/docs/api/books)). Related endpoints: `/works/{id}/editions.json`, `/works/{id}/ratings.json`, `/works/{id}/bookshelves.json`. The docs don't list Work field names. My live fetch returned `description`, `title`, `covers`, `subjects`, and `authors` (from observed response).
- **Images:** `https://covers.openlibrary.org/b/$key/$value-$size.jpg`, where key is `id`, `olid`, `isbn`, etc. and size is `S`, `M`, or `L`. Adding `?default=false` returns 404 instead of a blank image. Rate limit: "100 requests/IP are allowed for every 5 minutes", which applies to lookups **other than CoverID and OLID**. Over the limit you get **403**. Use the `cover_i` ID (`/b/id/{cover_i}-M.jpg`) to stay out of that limit. Covers are for display; "do not crawl our cover API" ([covers docs](https://openlibrary.org/dev/docs/api/covers)).
- **Key/account:** No key. Frequent callers should "Identify your application with a `User-Agent` header and `email`", for example `User-Agent: MyLibraryApp (contact@example.org)`. Registering your use case through a Google Form is optional ([developers/api](https://openlibrary.org/developers/api)).
- **Limits:** "Non-identified requests are limited to 1 per second", and identified requests get 3 per second. Breaking the limits "may result in aggressive rate limiting or blocking." Don't bulk-download through the API; use the monthly dumps instead. The API isn't meant as "a data backend for third-party services" or "a backend for high-traffic commercial services." Requests should be made on behalf of human users ([developers/api](https://openlibrary.org/developers/api)). A low-traffic class app where users search one at a time fits these rules.
- **Storage/caching:** "Cache responses whenever possible" ([developers/api](https://openlibrary.org/developers/api)). The Internet Archive "does not assert any new copyright or other proprietary rights over any of the material", with a caveat that "There may be existing rights issues on some contributions" ([licensing](https://openlibrary.org/developers/licensing)). No time limit on caching is stated.
- **Attribution:** None required. A link back is "appreciated" for covers ([covers docs](https://openlibrary.org/dev/docs/api/covers)).
- **Error behavior:** The status code for API-level rate limiting is **not verified** (only covers document 403). Plan to handle timeouts, 5xx, 403, and 429 generically.
- **Sample request (Fetched live 2026-11-14, HTTP 200):**
  `https://openlibrary.org/search.json?q=the+hobbit&fields=key,title,author_name,first_publish_year,cover_i&limit=3`
  The first result was `{"key":"/works/OL27482W","title":"The Hobbit","author_name":["J.R.R. Tolkien"],"first_publish_year":1937,"cover_i":14627509}`. The detail request `https://openlibrary.org/works/OL27482W.json` also returned 200.

### 3.2 Google Books

- **Search:** `GET https://www.googleapis.com/books/v1/volumes?q=...`. Supports `intitle:`, `inauthor:`, and `isbn:`. Pagination uses `startIndex` (0-based) and `maxResults` ("default is 10, and the maximum allowable value is 40") ([using](https://developers.google.com/books/docs/v1/using)).
- **Detail:** `GET https://www.googleapis.com/books/v1/volumes/{volumeId}`. Fields in `volumeInfo`: `title`, `authors`, `publisher`, `publishedDate`, `description`, `industryIdentifiers` (ISBN_10/13), `imageLinks` ([using](https://developers.google.com/books/docs/v1/using)).
- **Key:** "A request that does not provide an OAuth 2.0 token must send an API key." You create one in the Cloud Console under Credentials ([using](https://developers.google.com/books/docs/v1/using)). **Flag:** I sent a keyless request on 2026-11-14 and got **429 RESOURCE_EXHAUSTED** with `quota_limit_value: "0"`. In practice you need a key. Free quota numbers are **not verified**; they aren't stated on the docs pages I read.
- **Terms:** "You may not charge users any fee" ([Books terms](https://developers.google.com/books/terms)). The Google APIs ToS §5(e)(1) prohibits keeping "cached copies longer than permitted by the cache header" and also prohibits building databases or making permanent copies. §8(b) requires deleting cached content after termination ([Google APIs ToS](https://developers.google.com/terms)).
- **Attribution:** Show a "powered by Google" logo beside results, give each book a prominent link to its Google Books page or a preview, and "Don't reorder or otherwise change API results" ([branding](https://developers.google.com/books/branding)). The rule against changing results sits awkwardly with local sorting and filtering (req 5).
- **Sample (needs key):** `https://www.googleapis.com/books/v1/volumes?q=intitle:hobbit&maxResults=5&key=YOUR_KEY`

### 3.3 TheMealDB (recipes)

- **Search:** `https://www.themealdb.com/api/json/v1/1/search.php?s={name}`. `search.php?f={letter}` searches by first letter. **Detail:** `lookup.php?i={id}` ([api.php](https://www.themealdb.com/api.php)).
- **Fields (from live fetch; the docs page doesn't list them):** `idMeal`, `strMeal`, `strCategory`, `strArea`, `strInstructions`, `strMealThumb`, `strIngredient1..20`/`strMeasure1..20`.
- **Key:** The test key `1` can be used "during development of your app or for educational use", but "you must become a supporter if releasing publicly on an appstore" ([api.php](https://www.themealdb.com/api.php)). Premium-only features: multi-ingredient filters, `randomselection.php`, `latest.php`, and full database listing (otherwise capped at 100 items) ([api.php](https://www.themealdb.com/api.php)).
- **Limits:** Rate limit **not verified**; none is stated.
- **Storage:** Caching isn't addressed explicitly. The terms say "You can scrape, copy and modify any content returned from the API, as long as you use the official end points" and "You may use our API to lookup data and artwork for your development projects." For artwork you "must mention us as the source of the data" ([terms](https://www.themealdb.com/terms_of_use.php)).
- **Error behavior:** A search with no match returns **HTTP 200 with `{"meals":null}`** (observed live). Your code has to treat `null` as "no results", not as an error.
- **Sample (Fetched live 2026-11-14, HTTP 200):** `https://www.themealdb.com/api/json/v1/1/search.php?s=Arrabiata` returned `idMeal: "52771"`, "Spicy Arrabiata Penne". `lookup.php?i=52772` also returned 200.

### 3.4 Spoonacular (recipes)

- **Search:** `GET https://api.spoonacular.com/recipes/complexSearch?query=...&number=(1–100)&offset=(0–900)`. Cost: 1 point plus 0.01 points per result. **Detail:** `GET /recipes/{id}/information`, which returns `id`, `title`, `image`, `servings`, `readyInMinutes`, `sourceUrl`, `summary` and costs 1 point. Auth uses the `apiKey=` query parameter ([docs](https://spoonacular.com/food-api/docs)).
- **Free plan:** "50 points/day", 1 request/s, 2 concurrent. Going over returns **402** until midnight UTC. "no credit card required for the free plan" if you subscribe directly. The free plan is listed as "Backlink Required" ([pricing](https://spoonacular.com/food-api/pricing)).
- **Storage:** "You can indefinitely store the recipe id, the recipe title, and the recipe image url on your side. However, you may not store any other data from the spoonacular API, including but not limited to ingredients, instructions, nutritional information." Other data may be cached "(for a maximum of 1 hour)", and the terms add "With prior written permission". On termination you "must delete all data you ever obtained" ([terms](https://spoonacular.com/food-api/terms)).
- **Flag:** The terms describe free plans as invitation-only "for hackathons or academic use", but the pricing page shows a self-serve free plan. The two pages don't agree.
- **Sample (needs key):** `https://api.spoonacular.com/recipes/complexSearch?query=pasta&number=5&apiKey=YOUR_KEY`. Without a key it returns 401 JSON (observed).

### 3.5 Edamam (recipes, optional)

- The lowest plan listed is EnterpriseBasic at **$9/month** with a "10 days Trial period", 10,000 calls/month, throttled at "10/minute". Caching rule: "API subscribers can cache only the four basic macro nutrient datapoints." All plans require attribution ([recipe API page](https://developer.edamam.com/edamam-recipe-api)). Whether a credit card is required is **not verified**. **Edamam fails req 2 (no free tier), so I didn't evaluate it further.**

### 3.6 RAWG (video games)

- **Search:** `GET https://api.rawg.io/api/games?search=...`. Also supports `search_precise`, `search_exact` ([apidocs](https://rawg.io/apidocs)), `page`, `page_size`, and `ordering` (`name`, `released`, `added`, `created`, `updated`, `rating`, `metacritic`, with a `-` prefix to reverse) ([OpenAPI spec](https://api.rawg.io/docs/?format=openapi)).
- **Detail:** `GET /api/games/{id}` ("An ID or a slug identifying this Game"). Fields include `id`, `slug`, `name`, `description`, `metacritic`, `released`, `background_image`, `rating`, `playtime`, `added_by_status` ([OpenAPI spec](https://api.rawg.io/docs/?format=openapi)).
- **Key:** "Get API Key" on the docs page, passed as `key=`. The docs don't mention an approval wait ([apidocs](https://rawg.io/apidocs)).
- **Limits:** Free plan is "Non-commercial", up to 20,000 requests per month, with backlinks required ([apidocs](https://rawg.io/apidocs)). The ToS instead says it "is free for commercial use for projects and/or services within 20.000 requests per month", with "no more than 100.000 monthly active users or 500.000 page views per month" ([ToS](https://rawg.io/tos_api)). **Flag:** the docs page and the ToS disagree about commercial use.
- **Attribution:** "attribute RAWG as the source of the data and/or images" and "add an active hyperlink from every page where the data of RAWG is used" ([ToS](https://rawg.io/tos_api)).
- **Storage:** Not addressed explicitly. §6.2 says "no parts of the Services or the Content may be copied, reproduced, published, posted online" without consent, in the context of "publication, distribution or any other commercial purpose" ([ToS](https://rawg.io/tos_api)). Local storage for a class project is **unclear / not verified as permitted**.
- **Sample (needs key):** `https://api.rawg.io/api/games?search=portal&page_size=5&key=YOUR_KEY`. Without a key it returns `401 {"error": "The key parameter is not provided"}` (observed).

### 3.7 IGDB (video games, Twitch auth)

- **Setup:** "you must have a Twitch Account", "Ensure you have Two Factor Authentication enabled", register an app in the Twitch Developer Portal (Client Type "Confidential"), generate a Client Secret, then `POST https://id.twitch.tv/oauth2/token?client_id=...&client_secret=...&grant_type=client_credentials`. The token expires (`expires_in`) and "must be refreshed" ([IGDB docs](https://api-docs.igdb.com/)).
- **Requests:** `POST https://api.igdb.com/v4/games` with headers `Client-ID` and `Authorization: Bearer ...`. Example body: `search "Halo"; fields name,release_dates.human;`. Browser calls hit CORS errors, so the calls must come from Django ([IGDB docs](https://api-docs.igdb.com/)). Detail is the same endpoint with `where id = N;`.
- **Images:** `https://images.igdb.com/igdb/image/upload/t_{size}/{hash}.jpg`, for example `cover_big` (264x374) ([IGDB docs](https://api-docs.igdb.com/)).
- **Limits:** "rate limit of 4 requests per second", returning **429 Too Many Requests**, with "up to 8 open requests" ([IGDB docs](https://api-docs.igdb.com/)).
- **Commercial:** "free for non-commercial usage under the terms of the Twitch Developer Service Agreement". The FAQ says "The API is free for both non-commercial and commercial projects" (commercial use goes through the partner program) ([IGDB docs](https://api-docs.igdb.com/)).
- **Storage (best of all the candidates):** FAQ: "Am I allowed to store/cache the data locally? Yes. In fact, we prefer if you store and serve the data to your end users." ([IGDB docs](https://api-docs.igdb.com/))
- **Flag (recent change):** The docs announce a move from enums to tables, with a "Migration Period: starting on February 18 to August 31 (6 months)", after which "the old field names will be removed" ([IGDB docs](https://api-docs.igdb.com/)). The page doesn't state the year. Use the current field names.
- **Note:** WebFetch returned 403 for this page, so I read the official HTML with curl.
- **Sample (needs token):** `curl -X POST https://api.igdb.com/v4/games -H "Client-ID: YOUR_CLIENT_ID" -H "Authorization: Bearer YOUR_TOKEN" -d 'search "Halo"; fields name,first_release_date,cover.image_id,summary; limit 5;'`

### 3.8 TMDB (movies and TV)

- **Search:** `GET https://api.themoviedb.org/3/search/movie?query=...&page=&year=&include_adult=`. Returns `page`, `total_pages`, and `results[]` with `id`, `title`, `release_date`, `overview`, `poster_path` ([reference](https://developer.themoviedb.org/reference/search-movie)). **Detail:** `GET /3/movie/{id}` ([auth docs example](https://developer.themoviedb.org/docs/authentication-application)).
- **Images:** base URL from `/configuration`, for example `https://image.tmdb.org/t/p/w500/{poster_path}` ([image basics](https://developer.themoviedb.org/docs/image-basics)).
- **Key:** "click the API link from within your account settings page" and agree to the terms ([getting started](https://developer.themoviedb.org/docs/getting-started)). Auth is the `api_key` query param or a `Bearer` token ([auth](https://developer.themoviedb.org/docs/authentication-application)). Approval wait is **not verified** (not documented).
- **Limits:** The old 40-per-10-seconds limit was disabled on Dec 16, 2019. Current upper limits sit "somewhere in the 40 requests per second range". "respect the `429`" ([rate limiting](https://developer.themoviedb.org/docs/rate-limiting)).
- **Commercial:** "free to use for non-commercial purposes as long as you attribute TMDB" ([FAQ](https://developer.themoviedb.org/docs/faq)). The license "does not permit any commercial use" without a written agreement ([terms §2.A](https://www.themoviedb.org/api-terms-of-use)).
- **Storage:** Under prohibited uses, you may not "Cache, for longer than 6 months, any information obtained through or from TMDB or the TMDB APIs" (§1.C). On termination you must "promptly delete or otherwise purge all TMDB Content, including any cached content" (§1.D) ([terms](https://www.themoviedb.org/api-terms-of-use)). **This cap affects req 3:** saved movie metadata would need refreshing at least every 6 months.
- **Attribution:** Use the TMDB logo plus the notice "This [website...] uses TMDB and the TMDB APIs but is not endorsed, certified, or otherwise approved by TMDB" ([terms §3](https://www.themoviedb.org/api-terms-of-use)), placed in an "About" or "Credits" section ([FAQ](https://developer.themoviedb.org/docs/faq)).
- **Sample (needs key):** `https://api.themoviedb.org/3/search/movie?query=dune&api_key=YOUR_KEY`. Without a key it returns `401 {"status_code":7,...,"success":false}` (observed).

### 3.9 OMDb (movies)

- **Search:** `?s={title}&page=1–100`. **Detail:** `?i={imdbID}` (e.g. `tt1285016`) ([omdbapi.com](https://www.omdbapi.com/)). The docs page I read didn't list response fields. My live probes showed the error shape `{"Response":"False","Error":"..."}`.
- **Key:** request it at [apikey.aspx](https://www.omdbapi.com/apikey.aspx). The key arrives by email; the page warns of "Email Delays!" and says to contact the owner if it doesn't arrive within an hour. Free tier: "FREE! (1,000 daily limit)" ([apikey.aspx](https://www.omdbapi.com/apikey.aspx)).
- **Restrictions:** "The Poster API is only available to patrons". Content is "licensed under CC BY-NC 4.0" ([omdbapi.com](https://www.omdbapi.com/)). Storage/caching rules: **not verified** (not addressed).
- **Error behavior:** Invalid or missing key returns **401** with a JSON `Error` string (observed).
- **Sample (needs key):** `https://www.omdbapi.com/?s=batman&apikey=YOUR_KEY`

### 3.10 TVmaze (TV shows): runner-up

- **Search:** `/search/shows?q=:query` ("Search through all the shows in our database by the show's name"). `/singlesearch/shows?q=` "either returns exactly one result, or no result at all" ([api](https://www.tvmaze.com/api)).
- **Detail:** `/shows/:id` ("Retrieve all primary information for a given show"). There's also `/lookup/shows?imdb=:id` or `?thetvdb=:id`, which returns 301 on a match and 404 otherwise ([api](https://www.tvmaze.com/api)).
- **Fields (live fetch):** `id`, `name`, `type`, `language`, `genres`, `status`, `premiered`, `ended`, `rating.average`, `network`, `externals.imdb`, `image.medium`/`image.original`, `summary` (HTML), `url`. The docs say `image` is "a dictionary containing a "medium" and "original" key", or NULL ([api](https://www.tvmaze.com/api)).
- **Key:** None for the public API. The user-level API is for Premium members only ([api](https://www.tvmaze.com/api)).
- **Limits:** "API calls are rate limited to allow *at least* 20 calls every 10 seconds per IP address", with **429** when exceeded. Retry after a short pause ([api](https://www.tvmaze.com/api)).
- **Storage:** "Use of the TVmaze API is licensed by CC BY-SA … the data can freely be used for any purpose, as long as TVmaze is properly credited as source" and "your usage complies with the ShareAlike provision." "Images can safely be cached indefinitely", and the docs recommend caching images "on your own server" ([api](https://www.tvmaze.com/api)). Server responses are cached for 60 minutes; the live header was `Cache-Control: public, max-age=3600`.
- **Error behavior:** A missing show returns `404 {"name":"Not Found","message":"","code":0,"status":404}` (observed live).
- **Sample (Fetched live 2026-11-14, HTTP 200):** `https://api.tvmaze.com/search/shows?q=girls` returned show id 139, "Girls". `https://api.tvmaze.com/shows/1` returned 200 ("Under the Dome").

---

## 4. Requirement fit analysis (reqs 2, 3, 4, 8)

### Req 2: free enough for the whole project, quick setup
- **Instant, no key:** Open Library, TVmaze, TheMealDB (test key `1`).
- **Quick key, no card:** RAWG, TMDB, Spoonacular (direct signup), OMDb (emailed key, possible delay).
- **Heavier setup:** IGDB (Twitch, 2FA, app registration, expiring OAuth token) and Google Books (Cloud project; keyless calls are effectively blocked).
- **Too tight or paid:** Spoonacular's 50 points/day can run out during a demo or a test run. Edamam has no free tier.

### Req 3: saved items still show when the API is down
This depends on whether the terms let you **copy the fields into your own DB**:
- **Clearly allowed:** IGDB ("we prefer if you store"), TVmaze (CC BY-SA), Open Library ("Cache responses whenever possible", no new rights asserted).
- **Allowed with a limit:** TMDB (6-month cache cap, so add a `last_synced_at` field and a refresh path).
- **Effectively blocked:** Spoonacular (only id, title, and image URL indefinitely; ingredients and instructions max 1 hour) and Google Books (no keeping cache past the cache header, no "building databases").
- **Unclear:** RAWG, OMDb, TheMealDB (permissive language, but no explicit caching clause).
- **Images:** Storing an image *URL* means images break if the provider's CDN is down. That's acceptable if the template shows a placeholder when an image fails to load. TVmaze explicitly allows caching images on your own server.

### Req 4: user's own info on saved items
| Domain | Natural fields |
|---|---|
| Books (Open Library) | `status` (want to read / reading / finished / abandoned), `rating` 1–5, `current_page`, `started_on`, `finished_on`, `notes` |
| TV (TVmaze) | `status` (plan to watch / watching / completed / dropped), `current_season`, `current_episode`, `rating`, `notes` |
| Recipes (TheMealDB) | `status` (want to cook / cooked), `times_cooked`, `rating`, `my_modifications`, `last_cooked_on` |
| Games (RAWG/IGDB) | `status` (backlog / playing / beaten / dropped), `hours_played`, `platform_owned`, `rating`, `notes` |

### Req 8: helpful message when the provider is down or a request fails
What I observed or found documented:
- **429 rate limiting** is documented by TVmaze, IGDB, TMDB, and Google (observed). Open Library covers return **403**. Spoonacular returns **402** for an exhausted quota.
- **401 bad/missing key** came back as JSON from RAWG, TMDB, OMDb, and Spoonacular (observed). This is useful for showing a "server misconfigured" message instead of crashing.
- **No match, but HTTP 200:** TheMealDB (`{"meals":null}`). Open Library returns `numFound: 0`.
- **Not found:** TVmaze returns JSON 404.
- **Implementation pattern for any pick:** wrap calls in `requests.get(..., timeout=5)`. Catch `requests.Timeout`/`ConnectionError` and show "Book search is temporarily unavailable. Your saved books are still available below." Map 429/403 to "Too many searches, wait a moment." Map 5xx to "Provider is having trouble." Because saved items live in SQLite, the saved-items list and the app's own DRF API keep working whatever happens upstream.

---

## 5. Recommendation

**Use Open Library** for a personal reading tracker: search books, save them to "My Shelf", and track reading status, progress, rating, and notes.

Why:
1. **Req 2:** No key, no approval, no card. Setup is just a `User-Agent` header, so search works on day one.
2. **Req 3:** The terms encourage caching and assert no new rights. There's no time cap like TMDB's 6 months and no field whitelist like Spoonacular's.
3. **Req 4:** Reading status and progress are the textbook "user's own info" fields, and they're easy to filter and sort for req 5.
4. **Req 8:** Rate limits are documented (1–3 req/s for the API, 100 per 5 minutes on non-ID cover lookups with 403). The rate-limit status code for the main API isn't documented, so handle errors generically.
5. **Watch out for:** search schema "not guaranteed to be stable", so copy what you need. Respect the 1 req/s anonymous limit (send the `User-Agent`). Don't bulk-load.

**Pick TVmaze instead** if a TV watchlist interests you more. It's equally keyless, has explicit CC BY-SA storage rights, and the cleanest documented 429/404 behavior. Credit TVmaze with a link.

### Suggested local model fields (Open Library)
Copy these from the API response into a `Book` model, so the record stands on its own when the API is down:

| Model field | Source | Notes |
|---|---|---|
| `ol_work_key` (unique, indexed) | search `key`, e.g. `/works/OL27482W` | Stable external ID. Store just `OL27482W` and use it to prevent duplicates per user |
| `title` | `title` | |
| `authors` (CharField, comma-joined) or a related `Author` | `author_name[]` (+ `author_key[]`) | |
| `first_publish_year` (nullable int) | `first_publish_year` | Useful for sort and filter |
| `cover_id` (nullable int) | `cover_i` | Build the URL `https://covers.openlibrary.org/b/id/{cover_id}-M.jpg`. ID lookups avoid the 100/5-minute cover limit |
| `description` (TextField, blank) | work detail `description` (string or `{type,value}`) | Fetch once on save. Handle both shapes |
| `subjects` (optional) | work detail `subjects[]` | |
| `fetched_at` (DateTime) | set on save | Supports a later "refresh from API" |
| User fields | | `owner` FK to User, `status` (choices), `rating`, `current_page`, `notes`, `started_on`, `finished_on`, `created_at`, `updated_at` |

Make the record unique on `(owner, ol_work_key)`. Every queryset in views and DRF viewsets should filter by `owner=request.user` (req 6).

---

## 6. Sources (all accessed 2026-11-14)

- Open Library developer API: https://openlibrary.org/developers/api
- Open Library Search API: https://openlibrary.org/dev/docs/api/search
- Open Library Books/Works API: https://openlibrary.org/dev/docs/api/books
- Open Library Covers API: https://openlibrary.org/dev/docs/api/covers
- Open Library licensing: https://openlibrary.org/developers/licensing
- Google Books "Using the API": https://developers.google.com/books/docs/v1/using
- Google Books getting started: https://developers.google.com/books/docs/v1/getting_started
- Google Books terms: https://developers.google.com/books/terms
- Google Books branding: https://developers.google.com/books/branding
- Google APIs Terms of Service: https://developers.google.com/terms
- TheMealDB API: https://www.themealdb.com/api.php
- TheMealDB terms: https://www.themealdb.com/terms_of_use.php
- Spoonacular docs: https://spoonacular.com/food-api/docs
- Spoonacular pricing: https://spoonacular.com/food-api/pricing
- Spoonacular terms: https://spoonacular.com/food-api/terms
- Edamam Recipe API: https://developer.edamam.com/edamam-recipe-api
- RAWG API docs: https://rawg.io/apidocs
- RAWG OpenAPI spec: https://api.rawg.io/docs/?format=openapi
- RAWG API terms: https://rawg.io/tos_api
- IGDB API docs: https://api-docs.igdb.com/
- TMDB getting started: https://developer.themoviedb.org/docs/getting-started
- TMDB authentication: https://developer.themoviedb.org/docs/authentication-application
- TMDB rate limiting: https://developer.themoviedb.org/docs/rate-limiting
- TMDB FAQ: https://developer.themoviedb.org/docs/faq
- TMDB image basics: https://developer.themoviedb.org/docs/image-basics
- TMDB search movie reference: https://developer.themoviedb.org/reference/search-movie
- TMDB API terms of use: https://www.themoviedb.org/api-terms-of-use
- OMDb API: https://www.omdbapi.com/
- OMDb API key page: https://www.omdbapi.com/apikey.aspx
- TVmaze API: https://www.tvmaze.com/api
