import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


@pytest.mark.django_db
def test_payments_preview_happy_path():
    User = get_user_model()
    user = User.objects.create(email="u@example.com")
    user.set_password("x")
    user.save()

    book = Book.objects.create(
        title="A", author="B", cover="HARD", inventory=1, daily_fee="1.50"
    )
    today = date.today()
    borrowing = Borrowing.objects.create(
        user=user,
        book=book,
        borrow_date=today - timedelta(days=5),
        expected_return_date=today - timedelta(days=2),
    )

    c = APIClient()
    c.force_authenticate(user=user)
    r = c.get(f"/api/payments/preview/?borrowing={borrowing.id}")
    assert r.status_code == 200
    data = r.json()
    assert "amount" in data
    assert data["amount"] == "3.00"  # 2 days late * 1.50


@pytest.mark.django_db
def test_payments_create_happy_path_and_no_duplicates():
    User = get_user_model()
    user = User.objects.create(email="u2@example.com")
    user.set_password("x")
    user.save()

    book = Book.objects.create(
        title="C", author="D", cover="SOFT", inventory=1, daily_fee="1.50"
    )
    today = date.today()
    borrowing = Borrowing.objects.create(
        user=user,
        book=book,
        borrow_date=today - timedelta(days=5),
        expected_return_date=today - timedelta(days=2),
    )

    c = APIClient()
    c.force_authenticate(user=user)
    r1 = c.post("/api/payments/", {"borrowing": borrowing.id}, format="json")
    assert r1.status_code == 201
    data1 = r1.json()
    assert data1["borrowing"] == borrowing.id
    assert data1.get("amount") == "3.00"
    assert Payment.objects.count() == 1

    r2 = c.post("/api/payments/", {"borrowing": borrowing.id}, format="json")
    assert r2.status_code == 400


@pytest.mark.django_db
def test_payments_create_forbidden_for_other_user():
    User = get_user_model()
    owner = User.objects.create(email="owner@example.com")
    owner.set_password("x")
    owner.save()
    stranger = User.objects.create(email="stranger@example.com")
    stranger.set_password("x")
    stranger.save()

    book = Book.objects.create(
        title="E", author="F", cover="HARD", inventory=1, daily_fee="2.00"
    )
    today = date.today()
    borrowing = Borrowing.objects.create(
        user=owner,
        book=book,
        borrow_date=today - timedelta(days=3),
        expected_return_date=today - timedelta(days=1),
    )

    c = APIClient()
    c.force_authenticate(user=stranger)
    r = c.post("/api/payments/", {"borrowing": borrowing.id}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_payments_create_requires_borrowing_field():
    User = get_user_model()
    user = User.objects.create(email="need@example.com")
    user.set_password("x")
    user.save()

    c = APIClient()
    c.force_authenticate(user=user)
    r = c.post("/api/payments/", {}, format="json")
    assert r.status_code == 400
    body = r.json()
    assert "borrowing" in body


@pytest.mark.django_db
def test_payments_preview_requires_authentication():
    User = get_user_model()
    user = User.objects.create(email="anon@example.com")
    user.set_password("x")
    user.save()

    book = Book.objects.create(
        title="G", author="H", cover="SOFT", inventory=1, daily_fee="1.00"
    )
    today = date.today()
    borrowing = Borrowing.objects.create(
        user=user,
        book=book,
        borrow_date=today - timedelta(days=2),
        expected_return_date=today - timedelta(days=1),
    )

    c = APIClient()
    r = c.get(f"/api/payments/preview/?borrowing={borrowing.id}")
    assert r.status_code in (401, 403)
