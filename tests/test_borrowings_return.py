import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book
from borrowings.models import Borrowing

@pytest.mark.django_db
def test_return_happy_path():
    U = get_user_model()
    u = U.objects.create(email="u@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=1, daily_fee="1.00")
    c = APIClient(); c.force_authenticate(user=u)
    c.post("/api/borrowings/", {"borrow_date": str(date.today()),
                                "expected_return_date": str(date.today()+timedelta(days=1)),
                                "book": book.id}, format="json")
    book.refresh_from_db(); assert book.inventory == 0
    br = Borrowing.objects.latest("id")
    r = c.post(f"/api/borrowings/{br.id}/return/")
    assert r.status_code == 200
    book.refresh_from_db(); assert book.inventory == 1
    assert r.json()["actual_return_date"] is not None

@pytest.mark.django_db
def test_return_cannot_be_called_twice():
    U = get_user_model()
    u = U.objects.create(email="u2@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=1, daily_fee="1.00")
    c = APIClient(); c.force_authenticate(user=u)
    c.post("/api/borrowings/", {"borrow_date": str(date.today()),
                                "expected_return_date": str(date.today()+timedelta(days=1)),
                                "book": book.id}, format="json")
    br = Borrowing.objects.latest("id")
    assert c.post(f"/api/borrowings/{br.id}/return/").status_code == 200
    assert c.post(f"/api/borrowings/{br.id}/return/").status_code == 400

@pytest.mark.django_db
def test_user_cannot_return_others_borrowing():
    U = get_user_model()
    owner = U.objects.create(email="owner@example.com"); owner.set_password("x"); owner.save()
    stranger = U.objects.create(email="str@example.com"); stranger.set_password("x"); stranger.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=1, daily_fee="1.00")
    c_owner = APIClient(); c_owner.force_authenticate(user=owner)
    c_owner.post("/api/borrowings/", {"borrow_date": str(date.today()),
                                      "expected_return_date": str(date.today()+timedelta(days=1)),
                                      "book": book.id}, format="json")
    br = Borrowing.objects.latest("id")
    c_str = APIClient(); c_str.force_authenticate(user=stranger)
    assert c_str.post(f"/api/borrowings/{br.id}/return/").status_code == 403
