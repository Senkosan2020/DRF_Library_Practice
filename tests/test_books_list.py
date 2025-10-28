import pytest
from rest_framework.test import APIClient
from books.models import Book

@pytest.mark.django_db
def test_books_list_is_public():
    Book.objects.create(title="A", author="B", cover="HARD", inventory=1, daily_fee="1.00")
    c = APIClient()
    r = c.get("/api/books/")
    assert r.status_code == 200
    assert len(r.json()) == 1
