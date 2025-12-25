import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book

@pytest.mark.django_db
def test_borrowing_create_happy_path():
    U = get_user_model()
    u = U.objects.create(email="u@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=2, daily_fee="1.00")
    c = APIClient(); c.force_authenticate(user=u)
    r = c.post("/api/borrowings/", {
        "borrow_date": str(date.today()),
        "expected_return_date": str(date.today()+timedelta(days=3)),
        "book": book.id
    }, format="json")
    assert r.status_code == 201
    book.refresh_from_db(); assert book.inventory == 1

@pytest.mark.django_db
def test_borrowing_create_fails_when_inventory_zero():
    U = get_user_model()
    u = U.objects.create(email="u2@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=0, daily_fee="1.00")
    c = APIClient(); c.force_authenticate(user=u)
    r = c.post("/api/borrowings/", {
        "borrow_date": str(date.today()),
        "expected_return_date": str(date.today()+timedelta(days=1)),
        "book": book.id
    }, format="json")
    assert r.status_code == 400 and "book" in r.json()

@pytest.mark.django_db
def test_borrowing_create_invalid_dates():
    U = get_user_model()
    u = U.objects.create(email="u3@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=1, daily_fee="1.00")
    c = APIClient(); c.force_authenticate(user=u)
    r = c.post("/api/borrowings/", {
        "borrow_date": str(date.today()),
        "expected_return_date": str(date.today()-timedelta(days=1)),
        "book": book.id
    }, format="json")
    assert r.status_code == 400
