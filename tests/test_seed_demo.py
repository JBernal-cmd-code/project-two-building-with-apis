"""The seed_demo management command."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from books.models import SavedBook

pytestmark = pytest.mark.django_db


def run_seed():
    out = StringIO()
    call_command("seed_demo", stdout=out)
    return out.getvalue()


def test_running_seed_twice_does_not_duplicate_books():
    run_seed()
    demo = get_user_model().objects.get(username="demo")
    first_count = demo.saved_books.count()

    second_output = run_seed()

    assert first_count >= 20
    assert demo.saved_books.count() == first_count
    assert get_user_model().objects.filter(username="demo").count() == 1
    assert "Added 0 books" in second_output


def test_seed_creates_demo_user_with_a_varied_collection():
    output = run_seed()

    demo = get_user_model().objects.get(username="demo")
    books = demo.saved_books.all()
    assert 20 <= books.count() <= 30
    assert {b.status for b in books} == set(SavedBook.Status.values)
    assert any(b.rating for b in books) and any(b.rating is None for b in books)
    assert any(b.total_pages for b in books)
    assert any(b.total_pages is None for b in books)
    assert any(b.notes for b in books)
    assert 3 <= sum(b.cover_id is None for b in books) <= 5
    assert "demo" in output


def test_seed_prints_a_working_demo_password(client):
    output = run_seed()

    password = output.split("Demo password (local use only): ")[1].split()[0]
    assert client.login(username="demo", password=password)


def test_seed_books_pass_model_validation_and_use_short_work_keys():
    run_seed()

    for book in SavedBook.objects.all():
        book.full_clean()
        assert book.ol_work_key.startswith("OL")
        assert book.ol_work_key.endswith("W")


def test_seed_skips_only_books_the_demo_user_already_has(django_user_model):
    demo = django_user_model.objects.create_user(username="demo", password="x")
    SavedBook.objects.create(
        owner=demo, ol_work_key="OL27482W", title="The Hobbit", notes="My own note"
    )

    output = run_seed()

    hobbit = demo.saved_books.get(ol_work_key="OL27482W")
    assert hobbit.notes == "My own note"
    assert "skipped 1" in output
    assert demo.saved_books.filter(ol_work_key="OL27482W").count() == 1


def test_seed_does_not_touch_other_users_books(django_user_model):
    other = django_user_model.objects.create_user(username="other", password="x")
    SavedBook.objects.create(owner=other, ol_work_key="OL27482W", title="The Hobbit")

    run_seed()

    assert other.saved_books.count() == 1
