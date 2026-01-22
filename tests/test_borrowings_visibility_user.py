import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book
from borrowings.models import Borrowing
from datetime import date, timedelta

@pytest.mark.django_db
def test_user_sees_only_own_borrowings():
    U = get_user_model()
    u1 = U.objects.create(email="u1@example.com"); u1.set_password("x"); u1.save()
    u2 = U.objects.create(email="u2@example.com"); u2.set_password("x"); u2.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=3, daily_fee="1.00")
    today = date.today()
    Borrowing.objects.create(user=u1, book=book, borrow_date=today, expected_return_date=today+timedelta(days=1))
    Borrowing.objects.create(user=u2, book=book, borrow_date=today, expected_return_date=today+timedelta(days=1))
    c = APIClient(); c.force_authenticate(user=u1)
    r = c.get("/api/borrowings/")
    assert r.status_code == 200 and len(r.json()) == 1
