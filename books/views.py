"""Website views for saved books.

My Collection, book detail, edit, and remove use only local data and never
call Open Library. The search page is still a placeholder until Phase 4.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SavedBookEditForm


@login_required
def collection(request):
    # Privacy: every query starts from the current user's books.
    books = request.user.saved_books.all()
    return render(request, "books/collection.html", {"books": books})


def get_own_book(request, pk):
    """Another user's book is indistinguishable from one that doesn't exist."""
    return get_object_or_404(request.user.saved_books, pk=pk)


@login_required
def detail(request, pk):
    book = get_own_book(request, pk)
    if request.method == "POST":
        form = SavedBookEditForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Saved")
            return redirect(book)
        # Validation copied the rejected values onto the instance; show the
        # stored book in the header while the form keeps what was typed.
        book.refresh_from_db()
    else:
        form = SavedBookEditForm(instance=book)
    return render(request, "books/detail.html", {"book": book, "form": form})


@login_required
@require_POST
def delete(request, pk):
    book = get_own_book(request, pk)
    book.delete()
    messages.success(request, f"Removed '{book.title}' from your collection.")
    return redirect("books:collection")


@login_required
def search(request):
    return render(request, "books/placeholder.html", {"page_title": "Find books"})
