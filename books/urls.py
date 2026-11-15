from django.urls import path

from . import views

app_name = "books"

urlpatterns = [
    path("", views.collection, name="collection"),
    path("search/", views.search, name="search"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/delete/", views.delete, name="delete"),
]
