from django.contrib import admin

from .models import SavedBook


@admin.register(SavedBook)
class SavedBookAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "rating", "current_page", "total_pages")
    list_filter = ("status", "rating")
    search_fields = ("title", "authors", "ol_work_key", "owner__username")
