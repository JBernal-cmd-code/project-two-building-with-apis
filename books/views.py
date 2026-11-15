"""Website views for saved books.

My Collection uses only local data and never calls Open Library. The search
page is still a placeholder until Phase 4.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def collection(request):
    # Privacy: every query starts from the current user's books.
    books = request.user.saved_books.all()
    return render(request, "books/collection.html", {"books": books})


@login_required
def search(request):
    return render(request, "books/placeholder.html", {"page_title": "Find books"})
