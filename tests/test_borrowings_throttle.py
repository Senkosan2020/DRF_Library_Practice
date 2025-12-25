import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book
from borrowings.models import Borrowing

@pytest.mark.django_db
def test_create_throttle_per_user():
    U = get_user_model()
    u = U.objects.create(email="u@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=50, daily_fee="1.00")
    c = APIClient(); c.force_authenticate(user=u)

    payload = {"borrow_date": str(date.today()),
               "expected_return_date": str(date.today()+timedelta(days=1)),
               "book": book.id}

    for _ in range(5):
        r = c.post("/api/borrowings/", payload, format="json")
        assert r.status_code == 201

    r6 = c.post("/api/borrowings/", payload, format="json")
    assert r6.status_code == 429

@pytest.mark.django_db
def test_return_throttle_per_user():
    U = get_user_model()
    u = U.objects.create(email="u2@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="B", author="C", cover="SOFT", inventory=0, daily_fee="1.00")
    today = date.today()

    borrows = [
        Borrowing.objects.create(
            user=u, book=book,
            borrow_date=today, expected_return_date=today+timedelta(days=1)
        )
        for _ in range(6)
    ]
    c = APIClient(); c.force_authenticate(user=u)

    for i in range(5):
        r = c.post(f"/api/borrowings/{borrows[i].id}/return/")
        assert r.status_code == 200

    r6 = c.post(f"/api/borrowings/{borrows[5].id}/return/")
    assert r6.status_code == 429
