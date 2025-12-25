import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book
from borrowings.models import Borrowing
from datetime import date

@pytest.mark.django_db
def test_admin_sees_all_borrowings():
    U = get_user_model()
    admin = U.objects.create(email="a@example.com", is_staff=True); admin.set_password("x"); admin.save()
    u = U.objects.create(email="u@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=3, daily_fee="1.00")
    Borrowing.objects.create(user=admin, book=book, borrow_date=date.today(), expected_return_date=date.today())
    Borrowing.objects.create(user=u, book=book, borrow_date=date.today(), expected_return_date=date.today())
    c = APIClient(); c.force_authenticate(user=admin)
    r = c.get("/api/borrowings/")
    assert r.status_code == 200 and len(r.json()) == 2
