"""Create a ``demo`` user with about 25 realistic saved books.

The book data is written into this file and never fetched at run time, so the
command works offline. Work keys, cover IDs, and page counts are real Open
Library values, looked up once from the search API on 2026-11-14 (each cover
was checked with ``?default=false``). A few books deliberately have no cover
ID so the placeholder shows, and a few have no total pages.

Running the command again skips books the demo user already has.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from books.models import SavedBook

DEMO_USERNAME = "demo"
# Local development only. Never reuse this password anywhere real.
DEMO_PASSWORD = "chapter-demo-2026"

WANT = SavedBook.Status.WANT_TO_READ
READING = SavedBook.Status.READING
FINISHED = SavedBook.Status.FINISHED
DNF = SavedBook.Status.ABANDONED

# fmt: off
DEMO_BOOKS = [
    # Finished
    {"ol_work_key": "OL27482W", "title": "The Hobbit", "authors": "J.R.R. Tolkien",
     "first_publish_year": 1937, "cover_id": 14627509, "total_pages": 310,
     "status": FINISHED, "rating": 5,
     "notes": "Reread before starting the trilogy. Still perfect."},
    {"ol_work_key": "OL893414W", "title": "Dune", "authors": "Frank Herbert",
     "first_publish_year": 1965, "cover_id": 11481354, "total_pages": 608,
     "status": FINISHED, "rating": 4,
     "notes": "Slow first 100 pages, then I couldn't put it down."},
    {"ol_work_key": "OL66554W", "title": "Pride and Prejudice", "authors": "Jane Austen",
     "first_publish_year": 1813, "cover_id": 14348537, "total_pages": 351,
     "status": FINISHED, "rating": 5},
    {"ol_work_key": "OL1168083W", "title": "Nineteen Eighty-Four",
     "authors": "George Orwell", "first_publish_year": 1949, "cover_id": 9267242,
     "total_pages": 318, "status": FINISHED, "rating": 4},
    {"ol_work_key": "OL21745884W", "title": "Project Hail Mary", "authors": "Andy Weir",
     "first_publish_year": 2021, "cover_id": 11200092, "total_pages": 496,
     "status": FINISHED, "rating": 5, "notes": "Rocky!!"},
    {"ol_work_key": "OL59798W", "title": "A Wizard of Earthsea",
     "authors": "Ursula K. Le Guin", "first_publish_year": 1968, "cover_id": 13617691,
     "total_pages": 205, "status": FINISHED, "rating": 3},
    {"ol_work_key": "OL40873W", "title": "The Road", "authors": "Cormac McCarthy",
     "first_publish_year": 2006, "cover_id": None, "total_pages": 256,
     "status": FINISHED, "rating": 4, "notes": "Bleak but beautiful."},
    {"ol_work_key": "OL27258W", "title": "Neuromancer", "authors": "William Gibson",
     "first_publish_year": 1984, "cover_id": 283860, "total_pages": None,
     "status": FINISHED, "current_page": 0, "rating": None},
    # Reading
    {"ol_work_key": "OL27513W", "title": "The Fellowship of the Ring",
     "authors": "J.R.R. Tolkien", "first_publish_year": 1954, "cover_id": 14627060,
     "total_pages": 492, "status": READING, "current_page": 214},
    {"ol_work_key": "OL8479867W", "title": "The Name of the Wind",
     "authors": "Patrick Rothfuss, Marc Simonetti", "first_publish_year": 2007,
     "cover_id": 11480483, "total_pages": 736, "status": READING, "current_page": 88,
     "rating": 4},
    {"ol_work_key": "OL18139176W", "title": "Educated",
     "authors": "Tara Westover, Orah Danḳner", "first_publish_year": 2018,
     "cover_id": None, "total_pages": 384, "status": READING, "current_page": 301},
    {"ol_work_key": "OL17075811W", "title": "Sapiens", "authors": "Yuval Noah Harari",
     "first_publish_year": 2011, "cover_id": 8634250, "total_pages": None,
     "status": READING, "current_page": 140,
     "notes": "Library copy, due back on the 30th."},
    {"ol_work_key": "OL18012166W", "title": "Circe", "authors": "Madeline Miller",
     "first_publish_year": 2018, "cover_id": 8739376, "total_pages": 404,
     "status": READING, "current_page": 0},
    # Want to read
    {"ol_work_key": "OL3140822W", "title": "To Kill a Mockingbird",
     "authors": "Harper Lee", "first_publish_year": 1960, "cover_id": 14351077,
     "total_pages": 320, "status": WANT},
    {"ol_work_key": "OL450063W", "title": "Frankenstein; or, The Modern Prometheus",
     "authors": "Mary Shelley", "first_publish_year": 1818, "cover_id": 12356249,
     "total_pages": 240, "status": WANT,
     "notes": "Read before the book club meeting in December."},
    {"ol_work_key": "OL1095427W", "title": "Jane Eyre",
     "authors": "Charlotte Brontë", "first_publish_year": 1847, "cover_id": 8235363,
     "total_pages": 480, "status": WANT},
    {"ol_work_key": "OL17091839W", "title": "The Martian", "authors": "Andy Weir",
     "first_publish_year": 2011, "cover_id": 11447888, "total_pages": 407,
     "status": WANT},
    {"ol_work_key": "OL59800W", "title": "The Left Hand of Darkness",
     "authors": "Ursula K. Le Guin", "first_publish_year": 1969, "cover_id": 10618463,
     "total_pages": 304, "status": WANT},
    {"ol_work_key": "OL29983W", "title": "Little Women", "authors": "Louisa May Alcott",
     "first_publish_year": 1848, "cover_id": 8775559, "total_pages": None,
     "status": WANT},
    {"ol_work_key": "OL17202418W", "title": "Station Eleven",
     "authors": "Emily St. John Mandel", "first_publish_year": 2014,
     "cover_id": 7369961, "total_pages": 352, "status": WANT},
    {"ol_work_key": "OL2163649W", "title": "The Hitchhiker's Guide to the Galaxy",
     "authors": "Douglas Adams", "first_publish_year": 1979, "cover_id": 12986869,
     "total_pages": 216, "status": WANT},
    # Did not finish
    {"ol_work_key": "OL102749W", "title": "Moby Dick", "authors": "Herman Melville",
     "first_publish_year": 1851, "cover_id": None, "total_pages": 453,
     "status": DNF, "current_page": 162, "rating": 2,
     "notes": "Too many chapters about whale anatomy. Maybe someday."},
    {"ol_work_key": "OL468431W", "title": "The Great Gatsby",
     "authors": "F. Scott Fitzgerald", "first_publish_year": 1920,
     "cover_id": 10590366, "total_pages": 185, "status": DNF, "current_page": 40},
    {"ol_work_key": "OL50548W", "title": "Beloved", "authors": "Toni Morrison",
     "first_publish_year": 1987, "cover_id": None, "total_pages": 321,
     "status": DNF, "current_page": 75, "rating": 3,
     "notes": "Not the right time for this one. Want to come back to it."},
    {"ol_work_key": "OL64365W", "title": "Brave New World", "authors": "Aldous Huxley",
     "first_publish_year": 1932, "cover_id": 8231823, "total_pages": 241,
     "status": DNF, "current_page": 0},
]
# fmt: on


class Command(BaseCommand):
    help = "Create a demo user with about 25 saved books (works offline)."

    def handle(self, *args, **options):
        user, user_created = get_user_model().objects.get_or_create(
            username=DEMO_USERNAME
        )
        user.set_password(DEMO_PASSWORD)
        user.save()

        owned = set(user.saved_books.values_list("ol_work_key", flat=True))
        added = skipped = 0
        for data in DEMO_BOOKS:
            if data["ol_work_key"] in owned:
                skipped += 1
                continue
            book = SavedBook(owner=user, **data)
            book.full_clean()
            book.save()
            added += 1

        verb = "Created" if user_created else "Reused"
        self.stdout.write(f"{verb} user '{DEMO_USERNAME}'.")
        self.stdout.write(
            f"Added {added} books, skipped {skipped} already in the collection."
        )
        self.stdout.write(
            self.style.WARNING(f"Demo password (local use only): {DEMO_PASSWORD}")
        )
