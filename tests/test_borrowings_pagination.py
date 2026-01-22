import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book
from borrowings.models import Borrowing

@pytest.mark.django_db
def test_borrowings_list_not_paginated_by_default():
    U = get_user_model()
    u = U.objects.create(email="u@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=20, daily_fee="1.00")
    today = date.today()
    for i in range(5):
        Borrowing.objects.create(user=u, book=book, borrow_date=today, expected_return_date=today+timedelta(days=1))

    c = APIClient(); c.force_authenticate(user=u)
    r = c.get("/api/borrowings/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 5

@pytest.mark.django_db
def test_borrowings_list_paginated_when_limit_given():
    U = get_user_model()
    u = U.objects.create(email="u2@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=20, daily_fee="1.00")
    today = date.today()
    for i in range(5):
        Borrowing.objects.create(user=u, book=book, borrow_date=today, expected_return_date=today+timedelta(days=1))

    c = APIClient(); c.force_authenticate(user=u)
    r = c.get("/api/borrowings/?limit=2")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert data["count"] == 5
    assert len(data["results"]) == 2
