"""Saving a search result (/books/save/). Saving never calls Open Library."""

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from books.models import SavedBook

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"

HOBBIT_POST = {
    "ol_work_key": "OL27482W",
    "title": "The Hobbit",
    "authors": "J.R.R. Tolkien",
    "first_publish_year": "1937",
    "cover_id": "14627509",
    "total_pages": "310",
    "next": "/books/search/?q=the+hobbit",
}


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


@pytest.fixture
def other(django_user_model):
    return django_user_model.objects.create_user(username="other", password=PASSWORD)


@pytest.fixture(autouse=True)
def open_library_must_not_be_called(monkeypatch):
    """Saving uses only the posted facts; the network guard also blocks sockets."""
    from books import openlibrary

    def fail(*args, **kwargs):
        raise AssertionError("Saving must not call Open Library")

    monkeypatch.setattr(openlibrary, "search", fail)
    monkeypatch.setattr(openlibrary.requests, "get", fail)


def htmx_save(client, data):
    return client.post(reverse("books:save"), data, headers={"HX-Request": "true"})


def flashes(response):
    """Flash messages queued by a redirecting response (without following it)."""
    return [str(m) for m in get_messages(response.wsgi_request)]


def test_htmx_save_also_turns_the_cards_cover_and_title_into_links(client, reader):
    client.force_login(reader)

    response = htmx_save(client, HOBBIT_POST | {"ol_work_key": "/works/OL27482W"})

    html = response.content.decode()
    book = SavedBook.objects.get(owner=reader)
    # Out-of-band block, matched by id to the card's head on the search page.
    oob = html.split('id="result-head-OL27482W" hx-swap-oob="true"')[1]
    link = oob.split("data-owned-link>")[1].split("</a>")[0]
    assert f'href="{book.get_absolute_url()}"' in oob.split("data-owned-link>")[0]
    assert "14627509-M.jpg" in link  # the cover
    assert "The Hobbit</h3>" in link  # the title
    assert "data-openlibrary-link" not in html
    # The badge (the request's own target) comes before it, not out of band.
    assert html.index("In your collection") < html.index("hx-swap-oob")


def test_invalid_htmx_save_leaves_the_cards_cover_and_title_alone(client, reader):
    client.force_login(reader)

    response = htmx_save(client, HOBBIT_POST | {"title": ""})

    assert "hx-swap-oob" not in response.content.decode()


def test_save_requires_login(client):
    response = client.post(reverse("books:save"), HOBBIT_POST)

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))
    assert not SavedBook.objects.exists()


def test_save_rejects_get(client, reader):
    client.force_login(reader)

    response = client.get(reverse("books:save"), HOBBIT_POST)

    assert response.status_code == 405
    assert not SavedBook.objects.exists()


def test_save_copies_all_book_facts(client, reader):
    client.force_login(reader)

    htmx_save(client, HOBBIT_POST)

    book = SavedBook.objects.get(owner=reader)
    assert book.title == "The Hobbit"
    assert book.authors == "J.R.R. Tolkien"
    assert book.first_publish_year == 1937
    assert book.cover_id == 14627509
    assert book.current_page == 0
    assert book.rating is None


def test_save_with_missing_optional_facts(client, reader):
    client.force_login(reader)
    data = HOBBIT_POST | {
        "authors": "",
        "first_publish_year": "",
        "cover_id": "",
        "total_pages": "",
    }

    response = htmx_save(client, data)

    assert response.status_code == 200
    book = SavedBook.objects.get(owner=reader)
    assert book.authors == ""
    assert book.first_publish_year is None
    assert book.cover_id is None
    assert book.total_pages is None


def test_save_strips_works_prefix_and_treats_it_as_duplicate(client, reader):
    client.force_login(reader)
    htmx_save(client, HOBBIT_POST)

    response = htmx_save(client, HOBBIT_POST | {"ol_work_key": "/works/OL27482W"})

    assert "In your collection" in response.content.decode()
    assert SavedBook.objects.filter(owner=reader).count() == 1


def test_another_users_copy_does_not_block_saving(client, reader, other):
    theirs = SavedBook.objects.create(
        owner=other, ol_work_key="OL27482W", title="The Hobbit"
    )
    client.force_login(reader)

    response = htmx_save(client, HOBBIT_POST)

    mine = SavedBook.objects.get(owner=reader)
    assert mine.pk != theirs.pk
    assert f'href="{mine.get_absolute_url()}"' in response.content.decode()
    assert f'href="{theirs.get_absolute_url()}"' not in response.content.decode()


@pytest.mark.parametrize(
    "bad",
    [
        {"ol_work_key": "not-a-key"},
        {"ol_work_key": "OL27482M"},
        {"title": "   "},
        {"total_pages": "0"},
        {"cover_id": "abc"},
    ],
)
def test_invalid_htmx_save_returns_inline_error_and_no_row(client, reader, bad):
    client.force_login(reader)

    response = htmx_save(client, HOBBIT_POST | bad)

    html = response.content.decode()
    assert response.status_code == 200
    assert "data-save-error" in html
    assert "Couldn&#x27;t save this book" in html
    assert "data-save-form" in html  # the button stays so the card still works
    assert 'name="next" value="/books/search/?q=the+hobbit"' in html
    assert "<html" not in html
    assert not SavedBook.objects.exists()


def test_non_htmx_save_redirects_back_to_search_with_message(client, reader):
    client.force_login(reader)

    response = client.post(reverse("books:save"), HOBBIT_POST)

    assert response.status_code == 302
    assert response.url == "/books/search/?q=the+hobbit"
    assert flashes(response) == ["Saved 'The Hobbit' to your collection."]
    assert SavedBook.objects.filter(owner=reader).count() == 1


def test_non_htmx_duplicate_save_redirects_without_new_row(client, reader):
    client.force_login(reader)
    client.post(reverse("books:save"), HOBBIT_POST)

    response = client.post(reverse("books:save"), HOBBIT_POST)

    assert response.status_code == 302
    assert response.url == "/books/search/?q=the+hobbit"
    assert SavedBook.objects.filter(owner=reader).count() == 1


def test_non_htmx_invalid_save_redirects_back_with_error(client, reader):
    client.force_login(reader)

    response = client.post(reverse("books:save"), HOBBIT_POST | {"title": ""})

    assert response.status_code == 302
    assert response.url == "/books/search/?q=the+hobbit"
    assert flashes(response) == ["Couldn't save this book. Try searching again."]
    assert not SavedBook.objects.exists()


def test_non_htmx_save_ignores_offsite_return_url(client, reader):
    client.force_login(reader)

    response = client.post(
        reverse("books:save"), HOBBIT_POST | {"next": "https://evil.example/"}
    )

    assert response.status_code == 302
    assert response.url == reverse("books:search")


def test_htmx_save_creates_one_row_and_returns_badge_then_duplicate_adds_none(
    client, reader
):
    client.force_login(reader)

    first = htmx_save(client, HOBBIT_POST)

    assert SavedBook.objects.filter(owner=reader).count() == 1
    book = SavedBook.objects.get(owner=reader)
    assert book.ol_work_key == "OL27482W"
    assert book.status == SavedBook.Status.WANT_TO_READ
    assert book.total_pages == 310
    assert first.status_code == 200
    html = first.content.decode()
    assert "In your collection" in html
    assert f'href="{book.get_absolute_url()}"' in html
    assert "<html" not in html  # only the badge partial, not a whole page

    second = htmx_save(client, HOBBIT_POST)

    assert SavedBook.objects.filter(owner=reader).count() == 1
    assert second.status_code == 200
    assert "In your collection" in second.content.decode()
    assert f'href="{book.get_absolute_url()}"' in second.content.decode()
