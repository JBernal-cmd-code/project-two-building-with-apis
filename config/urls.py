from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("accounts/", include("accounts.urls")),
    path("books/", include("books.urls")),
    path("api/", include("books.api_urls")),
    path("admin/", admin.site.urls),
]
