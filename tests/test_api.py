"""The REST API: authentication, owner scoping, list, create, update, delete."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from books.models import SavedBook

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


@pytest.fixture
def other(django_user_model):
    return django_user_model.objects.create_user(username="other", password=PASSWORD)


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture(autouse=True)
def open_library_must_not_be_called(monkeypatch):
    """No API path calls Open Library; the network guard also blocks sockets."""
    from books import openlibrary

    def fail(*args, **kwargs):
        raise AssertionError("The API must not call Open Library")

    monkeypatch.setattr(openlibrary, "search", fail)
    monkeypatch.setattr(openlibrary.requests, "get", fail)


def save_book(owner, **fields):
    data = {"ol_work_key": "OL27482W", "title": "The Hobbit"} | fields
    return SavedBook.objects.create(owner=owner, **data)


def book_url(book):
    return reverse("api:book-detail", args=[book.pk])


LIST_URL = "/api/books/"


def test_every_method_on_another_users_book_returns_404(api, reader, other):
    book = save_book(reader, status="reading", current_page=10, total_pages=300)
    api.force_authenticate(other)
    url = book_url(book)

    get = api.get(url)
    put = api.put(
        url,
        {"ol_work_key": "OL27482W", "title": "Mine now", "status": "finished"},
        format="json",
    )
    patch = api.patch(url, {"status": "finished", "rating": 1}, format="json")
    delete = api.delete(url)

    assert [get.status_code, put.status_code, patch.status_code] == [404, 404, 404]
    assert delete.status_code == 404
    book.refresh_from_db()
    assert book.title == "The Hobbit"
    assert book.status == "reading"
    assert book.current_page == 10
    assert book.rating is None


def test_duplicate_create_returns_400_with_message(api, reader, other):
    save_book(reader, ol_work_key="OL27482W")
    save_book(other, ol_work_key="OL45883W", title="The Fellowship of the Ring")
    api.force_authenticate(reader)
    api.raise_request_exception = False  # a crash should show as the client's 500

    duplicate = api.post(
        LIST_URL, {"ol_work_key": "/works/OL27482W", "title": "The Hobbit"}
    )
    # Another user's copy doesn't block this user from saving the same book.
    saved_by_other = api.post(
        LIST_URL,
        {"ol_work_key": "OL45883W", "title": "The Fellowship of the Ring"},
    )

    assert duplicate.status_code == 400
    assert "This book is already in your collection." in str(duplicate.json())
    assert saved_by_other.status_code == 201
    assert reader.saved_books.count() == 2


def test_update_ignores_locked_fields_and_applies_model_rules(api, reader):
    book = save_book(
        reader,
        ol_work_key="OL27482W",
        title="The Hobbit",
        authors="J.R.R. Tolkien",
        first_publish_year=1937,
        cover_id=14627509,
        status="reading",
        current_page=50,
        total_pages=300,
    )
    api.force_authenticate(reader)
    url = book_url(book)

    too_far = api.patch(url, {"current_page": 301}, format="json")
    finished = api.patch(
        url,
        {
            "ol_work_key": "OL1W",
            "title": "Renamed",
            "authors": "Someone Else",
            "first_publish_year": 2001,
            "cover_id": 1,
            "status": "finished",
            "rating": 4,
        },
        format="json",
    )

    # While Reading, a page past the end is rejected.
    assert too_far.status_code == 400
    assert "current_page" in too_far.json()
    assert finished.status_code == 200
    book.refresh_from_db()
    assert (
        book.ol_work_key,
        book.title,
        book.authors,
        book.first_publish_year,
        book.cover_id,
    ) == ("OL27482W", "The Hobbit", "J.R.R. Tolkien", 1937, 14627509)
    assert (book.status, book.rating) == ("finished", 4)
    assert book.current_page == 300  # Finished auto-fill
    assert finished.json()["current_page"] == 300


# --- Authentication -------------------------------------------------------


def test_token_endpoint_returns_a_token_that_authenticates(api, reader):
    save_book(reader)

    response = api.post("/api/token/", {"username": "reader", "password": PASSWORD})
    token = response.json()["token"]
    api.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    listed = api.get(LIST_URL)

    assert response.status_code == 200
    assert listed.status_code == 200
    assert listed.json()["count"] == 1


def test_token_endpoint_rejects_a_wrong_password(api, reader):
    response = api.post("/api/token/", {"username": "reader", "password": "wrong"})

    assert response.status_code == 400
    assert "token" not in response.json()


def test_the_same_token_is_returned_each_time(api, reader):
    first = api.post("/api/token/", {"username": "reader", "password": PASSWORD})
    second = api.post("/api/token/", {"username": "reader", "password": PASSWORD})

    assert first.json()["token"] == second.json()["token"]


def test_a_bad_token_is_rejected(api, reader):
    api.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")

    assert api.get(LIST_URL).status_code == 401


def test_unauthenticated_requests_get_401_on_every_method(api, reader):
    book = save_book(reader)
    url = book_url(book)

    responses = [
        api.get(LIST_URL),
        api.post(LIST_URL, {"ol_work_key": "OL1W", "title": "X"}),
        api.get(url),
        api.put(url, {"status": "reading"}),
        api.patch(url, {"status": "reading"}),
        api.delete(url),
    ]

    assert [r.status_code for r in responses] == [401] * 6
    assert responses[0]["WWW-Authenticate"] == "Token"
    assert SavedBook.objects.count() == 1


def test_session_auth_works_and_the_browsable_api_renders(client, reader):
    save_book(reader)
    client.force_login(reader)

    json_response = client.get(LIST_URL)
    html_response = client.get(LIST_URL, headers={"Accept": "text/html"})

    assert json_response.status_code == 200
    assert json_response.json()["count"] == 1
    assert html_response.status_code == 200
    assert "Django REST framework" in html_response.content.decode()
    assert "The Hobbit" in html_response.content.decode()


# --- List ------------------------------------------------------------------


def save_many(owner, count, **fields):
    for n in range(1, count + 1):
        save_book(owner, ol_work_key=f"OL{n}W", title=f"Book {n:02d}", **fields)


def titles(response):
    return [book["title"] for book in response.json()["results"]]


def test_list_returns_only_the_owners_books(api, reader, other):
    save_book(reader, title="Mine")
    save_book(other, title="Theirs")
    api.force_authenticate(reader)

    response = api.get(LIST_URL)

    assert response.status_code == 200
    assert titles(response) == ["Mine"]
    assert "owner" not in response.json()["results"][0]


def test_list_is_paginated_20_per_page_with_count_next_and_previous(api, reader):
    save_many(reader, 25)
    api.force_authenticate(reader)

    first = api.get(LIST_URL)
    second = api.get(first.json()["next"])

    assert first.json()["count"] == 25
    assert len(first.json()["results"]) == 20
    assert first.json()["previous"] is None
    assert "page=2" in first.json()["next"]
    assert len(second.json()["results"]) == 5
    assert second.json()["next"] is None
    assert second.json()["previous"] is not None


def test_next_link_keeps_the_filters_and_ordering(api, reader):
    save_many(reader, 25, status="reading", rating=4)
    api.force_authenticate(reader)

    response = api.get(
        LIST_URL,
        {"q": "book", "status": "reading", "min_rating": 4, "ordering": "title"},
    )
    next_url = response.json()["next"]

    for part in ("q=book", "status=reading", "min_rating=4", "ordering=title"):
        assert part in next_url
    assert titles(api.get(next_url))[0] == "Book 21"


def test_out_of_range_page_shows_the_last_page_and_invalid_shows_page_1(api, reader):
    save_many(reader, 25)
    api.force_authenticate(reader)

    out_of_range = api.get(LIST_URL, {"page": 99})
    invalid = api.get(LIST_URL, {"page": "abc"})

    assert out_of_range.status_code == 200
    assert len(out_of_range.json()["results"]) == 5
    assert invalid.status_code == 200
    assert len(invalid.json()["results"]) == 20
    assert invalid.json()["previous"] is None


def test_list_search_matches_title_or_authors_ignoring_case(api, reader):
    save_book(reader, ol_work_key="OL1W", title="The Hobbit", authors="Tolkien")
    save_book(reader, ol_work_key="OL2W", title="Dune", authors="Frank Herbert")
    save_book(reader, ol_work_key="OL3W", title="Emma", authors="Jane Austen")
    api.force_authenticate(reader)

    by_title = api.get(LIST_URL, {"q": "HOBBIT"})
    by_author = api.get(LIST_URL, {"q": "herbert"})

    assert titles(by_title) == ["The Hobbit"]
    assert titles(by_author) == ["Dune"]


def test_list_filters_by_status_and_minimum_rating(api, reader):
    save_book(reader, ol_work_key="OL1W", title="A", status="reading", rating=5)
    save_book(reader, ol_work_key="OL2W", title="B", status="reading", rating=3)
    save_book(reader, ol_work_key="OL3W", title="C", status="finished", rating=5)
    api.force_authenticate(reader)

    reading = api.get(LIST_URL, {"status": "reading", "ordering": "title"})
    four_up = api.get(LIST_URL, {"min_rating": 4, "ordering": "title"})

    assert titles(reading) == ["A", "B"]
    assert titles(four_up) == ["A", "C"]


def test_list_orderings_match_the_website(api, reader):
    save_book(reader, ol_work_key="OL1W", title="Beta", rating=3)
    save_book(reader, ol_work_key="OL2W", title="Alpha")
    save_book(reader, ol_work_key="OL3W", title="Gamma", rating=5)
    api.force_authenticate(reader)

    by_title = api.get(LIST_URL, {"ordering": "title"})
    by_rating = api.get(LIST_URL, {"ordering": "-rating"})
    newest = api.get(LIST_URL)

    assert titles(by_title) == ["Alpha", "Beta", "Gamma"]
    assert titles(by_rating) == ["Gamma", "Beta", "Alpha"]  # unrated last
    assert titles(newest) == ["Gamma", "Alpha", "Beta"]  # default -created_at


def test_list_combines_filters_and_ordering(api, reader):
    save_book(
        reader,
        ol_work_key="OL1W",
        title="Two Towers",
        authors="Tolkien",
        status="reading",
        rating=4,
    )
    save_book(
        reader,
        ol_work_key="OL2W",
        title="Hobbit",
        authors="Tolkien",
        status="reading",
        rating=5,
    )
    save_book(
        reader,
        ol_work_key="OL3W",
        title="Silmarillion",
        authors="Tolkien",
        status="reading",
        rating=3,
    )
    save_book(
        reader,
        ol_work_key="OL4W",
        title="Dune",
        authors="Herbert",
        status="reading",
        rating=5,
    )
    save_book(
        reader,
        ol_work_key="OL5W",
        title="Fellowship",
        authors="Tolkien",
        status="finished",
        rating=5,
    )
    api.force_authenticate(reader)

    response = api.get(
        LIST_URL,
        {"q": "tolkien", "status": "reading", "min_rating": 4, "ordering": "title"},
    )

    assert titles(response) == ["Hobbit", "Two Towers"]


def test_unknown_list_parameters_fall_back_to_defaults(api, reader):
    save_book(reader, ol_work_key="OL1W", title="Older")
    save_book(reader, ol_work_key="OL2W", title="Newer", status="reading")
    api.force_authenticate(reader)

    response = api.get(
        LIST_URL, {"status": "lost", "min_rating": "9", "ordering": "owner"}
    )

    assert response.status_code == 200
    assert titles(response) == ["Newer", "Older"]


# --- Create ----------------------------------------------------------------


def test_create_sets_the_owner_from_the_request_and_ignores_input_owner(
    api, reader, other
):
    api.force_authenticate(reader)

    response = api.post(
        LIST_URL,
        {
            "ol_work_key": "/works/OL27482W",
            "title": "The Hobbit",
            "authors": "J.R.R. Tolkien",
            "first_publish_year": 1937,
            "cover_id": 14627509,
            "total_pages": 310,
            "owner": other.pk,
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ol_work_key"] == "OL27482W"
    assert body["status"] == "want_to_read"
    assert body["current_page"] == 0
    book = SavedBook.objects.get(pk=body["id"])
    assert book.owner == reader
    assert book.ol_work_key == "OL27482W"
    assert (book.authors, book.first_publish_year, book.cover_id) == (
        "J.R.R. Tolkien",
        1937,
        14627509,
    )
    assert book.total_pages == 310
    assert other.saved_books.count() == 0


def test_create_with_only_key_and_title_leaves_optional_facts_empty(api, reader):
    api.force_authenticate(reader)

    response = api.post(LIST_URL, {"ol_work_key": "OL27482W", "title": "The Hobbit"})

    assert response.status_code == 201
    body = response.json()
    assert body["authors"] == ""
    assert body["first_publish_year"] is None
    assert body["cover_id"] is None
    assert body["total_pages"] is None
    assert body["rating"] is None


@pytest.mark.parametrize(
    "work_key", ["", "OL27482", "27482W", "OL27482M", "/books/OL27482W", "OLxW"]
)
def test_create_rejects_invalid_work_keys(api, reader, work_key):
    api.force_authenticate(reader)

    response = api.post(LIST_URL, {"ol_work_key": work_key, "title": "The Hobbit"})

    assert response.status_code == 400
    assert "ol_work_key" in response.json()
    assert SavedBook.objects.count() == 0


def test_create_rejects_a_missing_work_key(api, reader):
    api.force_authenticate(reader)

    response = api.post(LIST_URL, {"title": "The Hobbit"})

    assert response.status_code == 400
    assert "ol_work_key" in response.json()


@pytest.mark.parametrize("title", [None, "", "   "])
def test_create_rejects_a_missing_or_blank_title(api, reader, title):
    api.force_authenticate(reader)
    data = {"ol_work_key": "OL27482W"}
    if title is not None:
        data["title"] = title

    response = api.post(LIST_URL, data)

    assert response.status_code == 400
    assert "title" in response.json()
    assert SavedBook.objects.count() == 0


@pytest.mark.parametrize(
    ("fields", "error_field"),
    [
        ({"rating": 6}, "rating"),
        ({"rating": 0}, "rating"),
        ({"total_pages": 0}, "total_pages"),
        ({"current_page": -1}, "current_page"),
        ({"current_page": 400, "total_pages": 300}, "current_page"),
        ({"status": "lost"}, "status"),
    ],
)
def test_create_applies_the_model_rules(api, reader, fields, error_field):
    api.force_authenticate(reader)

    response = api.post(
        LIST_URL,
        {"ol_work_key": "OL27482W", "title": "The Hobbit"} | fields,
        format="json",
    )

    assert response.status_code == 400
    assert error_field in response.json()
    assert SavedBook.objects.count() == 0


def test_create_as_finished_fills_in_the_current_page(api, reader):
    api.force_authenticate(reader)

    response = api.post(
        LIST_URL,
        {
            "ol_work_key": "OL27482W",
            "title": "The Hobbit",
            "status": "finished",
            "total_pages": 310,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["current_page"] == 310


# --- Retrieve, update, delete ----------------------------------------------


def test_retrieve_returns_the_book(api, reader):
    book = save_book(reader, authors="J.R.R. Tolkien", rating=5, notes="Loved it")
    api.force_authenticate(reader)

    response = api.get(book_url(book))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == book.pk
    assert (body["title"], body["authors"], body["rating"], body["notes"]) == (
        "The Hobbit",
        "J.R.R. Tolkien",
        5,
        "Loved it",
    )


def test_full_update_replaces_the_tracking_fields(api, reader):
    book = save_book(reader, status="reading", current_page=10, rating=2, notes="x")
    api.force_authenticate(reader)

    response = api.put(
        book_url(book),
        {
            "status": "abandoned",
            "current_page": 40,
            "total_pages": 300,
            "rating": None,
            "notes": "Not for me",
        },
        format="json",
    )

    assert response.status_code == 200
    book.refresh_from_db()
    assert (book.status, book.current_page, book.total_pages) == ("abandoned", 40, 300)
    assert book.rating is None
    assert book.notes == "Not for me"
    assert book.title == "The Hobbit"


def test_partial_update_changes_only_the_sent_fields(api, reader):
    book = save_book(reader, status="reading", current_page=10, notes="Keep me")
    api.force_authenticate(reader)

    response = api.patch(book_url(book), {"rating": 3}, format="json")

    assert response.status_code == 200
    book.refresh_from_db()
    assert book.rating == 3
    assert (book.status, book.current_page, book.notes) == ("reading", 10, "Keep me")


@pytest.mark.parametrize(
    "fields", [{"rating": 6}, {"total_pages": 0}, {"current_page": 301}]
)
def test_invalid_update_is_rejected_and_not_saved(api, reader, fields):
    book = save_book(reader, status="reading", current_page=10, total_pages=300)
    api.force_authenticate(reader)

    response = api.patch(book_url(book), fields, format="json")

    assert response.status_code == 400
    book.refresh_from_db()
    assert (book.current_page, book.total_pages, book.rating) == (10, 300, None)


def test_lowering_total_pages_below_the_current_page_is_rejected(api, reader):
    book = save_book(reader, status="reading", current_page=200, total_pages=300)
    api.force_authenticate(reader)

    response = api.patch(book_url(book), {"total_pages": 150}, format="json")

    assert response.status_code == 400
    assert "current_page" in response.json()
    book.refresh_from_db()
    assert book.total_pages == 300


def test_delete_removes_the_book(api, reader):
    book = save_book(reader)
    api.force_authenticate(reader)

    response = api.delete(book_url(book))

    assert response.status_code == 204
    assert not SavedBook.objects.filter(pk=book.pk).exists()
    assert api.get(book_url(book)).status_code == 404
