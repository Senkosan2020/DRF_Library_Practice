import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book
from borrowings.models import Borrowing

@pytest.mark.django_db
def test_filter_is_active():
    U = get_user_model()
    u = U.objects.create(email="u@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=2, daily_fee="1.00")
    today = date.today()
    b1 = Borrowing.objects.create(user=u, book=book, borrow_date=today, expected_return_date=today+timedelta(days=1))
    b2 = Borrowing.objects.create(user=u, book=book, borrow_date=today, expected_return_date=today+timedelta(days=1), actual_return_date=today)
    c = APIClient(); c.force_authenticate(user=u)
    assert len(c.get("/api/borrowings/?is_active=true").json()) == 1
    assert len(c.get("/api/borrowings/?is_active=false").json()) == 1

@pytest.mark.django_db
def test_filter_user_id_admin_only():
    U = get_user_model()
    admin = U.objects.create(email="a@example.com", is_staff=True); admin.set_password("x"); admin.save()
    u1 = U.objects.create(email="u1@example.com"); u1.set_password("x"); u1.save()
    u2 = U.objects.create(email="u2@example.com"); u2.set_password("x"); u2.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=3, daily_fee="1.00")
    today = date.today()
    Borrowing.objects.create(user=u1, book=book, borrow_date=today, expected_return_date=today)
    Borrowing.objects.create(user=u2, book=book, borrow_date=today, expected_return_date=today)
    c = APIClient(); c.force_authenticate(user=admin)
    r = c.get(f"/api/borrowings/?user_id={u1.id}")
    assert r.status_code == 200 and all(x["user"] == u1.id for x in r.json())
