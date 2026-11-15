"""My Collection page: privacy and the basic cover grid."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from books.models import SavedBook

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


@pytest.fixture
def other(django_user_model):
    return django_user_model.objects.create_user(username="other", password=PASSWORD)


def save_book(owner, **fields):
    data = {"ol_work_key": "OL27482W", "title": "The Hobbit"} | fields
    return SavedBook.objects.create(owner=owner, **data)


def test_collection_shows_only_the_logged_in_users_books(client, reader, other):
    save_book(reader, ol_work_key="OL893414W", title="Dune")
    save_book(other, ol_work_key="OL66554W", title="Pride and Prejudice")
    # Same work saved by both users: only the reader's own copy may appear.
    save_book(reader, ol_work_key="OL27482W", title="The Hobbit")
    save_book(other, ol_work_key="OL27482W", title="The Hobbit")
    client.force_login(reader)

    response = client.get(reverse("books:collection"))

    html = response.content.decode()
    assert response.status_code == 200
    assert "Dune" in html
    assert "Pride and Prejudice" not in html
    assert html.count("data-book-card") == 2


def get_collection(client, user):
    client.force_login(user)
    response = client.get(reverse("books:collection"))
    assert response.status_code == 200
    return response.content.decode()


def test_collection_requires_login(client):
    url = reverse("books:collection")

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('accounts:login')}?next={url}"


def test_book_with_cover_shows_image_with_placeholder_fallback(client, reader):
    save_book(reader, cover_id=14627509)

    html = get_collection(client, reader)

    assert 'src="https://covers.openlibrary.org/b/id/14627509-M.jpg"' in html
    # A failed load hides the image and reveals the placeholder next to it.
    assert "onerror=" in html
    assert "this.nextElementSibling.hidden=false" in html
    assert "data-cover-placeholder" in html


def test_book_without_cover_shows_placeholder_and_no_image(client, reader):
    save_book(reader, title="Moby Dick", cover_id=None)

    html = get_collection(client, reader)

    assert "covers.openlibrary.org" not in html
    assert "<img" not in html
    assert "data-cover-placeholder" in html
    assert "No cover" in html


def test_missing_authors_show_unknown_author(client, reader):
    save_book(reader, authors="")

    assert "Unknown author" in get_collection(client, reader)


def results_part(html):
    """The results section, without the sidebar (whose rating filter has stars)."""
    return html.split("data-collection-results", 1)[1]


def test_rated_book_shows_stars_and_unrated_book_shows_none(client, reader, other):
    save_book(reader, rating=4)
    save_book(other, rating=None)

    rated_html = results_part(get_collection(client, reader))
    unrated_html = results_part(get_collection(client, other))

    assert 'aria-label="4 of 5 stars"' in rated_html
    assert "★" not in unrated_html
    assert "Not rated" not in unrated_html


@pytest.mark.parametrize(
    ("fields", "shown"),
    [
        ({"status": "reading", "total_pages": 300, "current_page": 150}, True),
        ({"status": "abandoned", "total_pages": 300, "current_page": 30}, True),
        ({"status": "finished", "total_pages": 300}, True),
        ({"status": "want_to_read", "total_pages": 300, "current_page": 50}, False),
        ({"status": "reading", "total_pages": 300, "current_page": 0}, False),
        ({"status": "reading", "total_pages": None, "current_page": 120}, False),
    ],
)
def test_progress_bar_only_shows_when_there_is_progress(client, reader, fields, shown):
    save_book(reader, **fields)

    html = get_collection(client, reader)

    assert ("data-progress" in html) is shown


def test_progress_bar_shows_the_percentage(client, reader):
    save_book(reader, status="reading", total_pages=300, current_page=150)

    html = get_collection(client, reader)

    assert 'value="50"' in html
    assert "50%" in html


@pytest.mark.parametrize(
    ("status", "label", "color"),
    [
        ("want_to_read", "Want to read", "badge-secondary"),
        ("reading", "Reading", "badge-info"),
        ("finished", "Finished", "badge-success"),
        ("abandoned", "Did not finish", "badge-warning"),
    ],
)
def test_each_status_badge_has_its_color(client, reader, status, label, color):
    save_book(reader, status=status)

    html = get_collection(client, reader)

    assert color in html
    assert label in html


def test_card_title_shows_the_full_title_on_hover(client, reader):
    long_title = "The Hitchhiker's Guide to the Galaxy"
    save_book(reader, title=long_title)

    html = get_collection(client, reader)

    assert 'title="The Hitchhiker&#x27;s Guide to the Galaxy"' in html


def test_titles_are_escaped(client, reader):
    save_book(reader, title="<script>alert(1)</script>")

    html = get_collection(client, reader)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_empty_collection_shows_friendly_message(client, reader):
    html = get_collection(client, reader)

    assert "data-empty-collection" in html
    assert "Your collection is empty" in html


def test_seeded_collection_renders_without_open_library(client):
    # The autouse network guard fails this test if the page reaches out.
    call_command("seed_demo", stdout=StringIO())
    demo = get_user_model().objects.get(username="demo")

    first_page = get_collection(client, demo)
    second_page = client.get(reverse("books:collection"), {"page": 2}).content.decode()

    cards = first_page.count("data-book-card") + second_page.count("data-book-card")
    assert cards == demo.saved_books.count()
