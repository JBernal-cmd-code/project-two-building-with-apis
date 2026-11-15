"""Accounts: sign-up, login, logout, and login-required redirects."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"


def test_signup_creates_user_and_logs_them_in(client):
    response = client.post(
        reverse("accounts:signup"),
        {"username": "reader", "password1": PASSWORD, "password2": PASSWORD},
    )

    user = get_user_model().objects.filter(username="reader").first()
    assert user is not None, "sign-up did not create the user"
    assert user.check_password(PASSWORD)
    assert response.status_code == 302
    assert response.url == reverse("books:collection")
    # The next request is made as the new user, with no separate login step.
    assert client.get(reverse("home")).context["user"] == user


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


def test_protected_page_redirects_to_login_then_back(client, reader):
    search_url = reverse("books:search")
    login_url = reverse("accounts:login")

    response = client.get(search_url)
    assert response.status_code == 302
    assert response.url == f"{login_url}?next={search_url}"

    response = client.post(
        login_url,
        {"username": "reader", "password": PASSWORD, "next": search_url},
    )
    assert response.status_code == 302
    assert response.url == search_url
    assert client.get(search_url).status_code == 200


def test_login_page_carries_return_to_parameter(client):
    response = client.get(reverse("accounts:login"), {"next": "/books/search/"})

    assert 'name="next" value="/books/search/"' in response.content.decode()


def test_login_with_valid_credentials(client, reader):
    response = client.post(
        reverse("accounts:login"), {"username": "reader", "password": PASSWORD}
    )

    assert response.status_code == 302
    assert response.url == reverse("books:collection")
    assert client.get(reverse("home")).context["user"] == reader


def test_login_with_wrong_password_shows_error(client, reader):
    response = client.post(
        reverse("accounts:login"), {"username": "reader", "password": "wrong"}
    )

    assert response.status_code == 200
    assert "Please enter a correct username and password" in response.content.decode()
    assert not response.context["user"].is_authenticated


def test_logout_ends_session(client, reader):
    client.force_login(reader)

    response = client.post(reverse("accounts:logout"), follow=True)

    assert response.redirect_chain[-1][0] == reverse("home")
    assert not response.context["user"].is_authenticated
    assert client.get(reverse("books:collection")).status_code == 302


def test_logout_requires_post(client, reader):
    client.force_login(reader)

    response = client.get(reverse("accounts:logout"))

    assert response.status_code == 405
    assert client.get(reverse("home")).context["user"] == reader


def test_signup_rejects_mismatched_passwords(client):
    response = client.post(
        reverse("accounts:signup"),
        {"username": "reader", "password1": PASSWORD, "password2": "different-42-X"},
    )

    assert response.status_code == 200
    assert "didn’t match" in response.content.decode()
    assert not get_user_model().objects.filter(username="reader").exists()
