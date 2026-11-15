"""URLs for the REST API, mounted at ``/api/``."""

from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .api import SavedBookViewSet

app_name = "api"

router = DefaultRouter()
router.register("books", SavedBookViewSet, basename="book")

urlpatterns = [
    path("token/", obtain_auth_token, name="token"),
    *router.urls,
]
