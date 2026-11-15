"""Public home page and the shared base layout."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"


def test_home_page_loads_for_logged_out_visitor(client):
    response = client.get(reverse("home"))

    html = response.content.decode()
    assert response.status_code == 200
    assert "Your private reading record" in html
    assert reverse("accounts:signup") in html
    assert reverse("accounts:login") in html


def test_navbar_shows_app_links_and_logout_when_logged_in(client, django_user_model):
    user = django_user_model.objects.create_user(username="reader", password=PASSWORD)
    client.force_login(user)

    html = client.get(reverse("home")).content.decode()

    assert "MyChapterCollection" in html
    assert f'href="{reverse("books:search")}"' in html
    assert f'href="{reverse("books:collection")}"' in html
    assert f'action="{reverse("accounts:logout")}"' in html


def test_flash_message_after_signup_renders_in_base_layout(client):
    response = client.post(
        reverse("accounts:signup"),
        {"username": "reader", "password1": PASSWORD, "password2": PASSWORD},
        follow=True,
    )

    html = response.content.decode()
    assert 'role="alert"' in html
    assert "Welcome, reader! Your collection is ready." in html


def test_flash_message_after_login_renders_in_base_layout(client, django_user_model):
    django_user_model.objects.create_user(username="reader", password=PASSWORD)

    response = client.post(
        reverse("accounts:login"),
        {"username": "reader", "password": PASSWORD},
        follow=True,
    )

    html = response.content.decode()
    assert 'role="alert"' in html
    assert "Welcome back, reader!" in html


def test_failed_login_shows_no_welcome_message(client, django_user_model):
    django_user_model.objects.create_user(username="reader", password=PASSWORD)

    response = client.post(
        reverse("accounts:login"),
        {"username": "reader", "password": "wrong"},
        follow=True,
    )

    assert "Welcome back" not in response.content.decode()


def test_signup_shows_only_the_signup_welcome(client):
    response = client.post(
        reverse("accounts:signup"),
        {"username": "reader", "password1": PASSWORD, "password2": PASSWORD},
        follow=True,
    )

    assert "Welcome back" not in response.content.decode()


def test_flash_message_after_logout_renders_on_home_page(client, django_user_model):
    user = django_user_model.objects.create_user(username="reader", password=PASSWORD)
    client.force_login(user)

    response = client.post(reverse("accounts:logout"), follow=True)

    assert "You&#x27;ve been logged out." in response.content.decode()
