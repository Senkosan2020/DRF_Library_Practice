import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from books.models import Book
from borrowings.models import Borrowing

@pytest.mark.django_db
def test_filter_overdue_true_false():
    U = get_user_model()
    u = U.objects.create(email="u@example.com"); u.set_password("x"); u.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=10, daily_fee="1.00")

    today = date.today()
    Borrowing.objects.create(
        user=u, book=book,
        borrow_date=today - timedelta(days=5),
        expected_return_date=today - timedelta(days=2),
        actual_return_date=None
    )
    Borrowing.objects.create(
        user=u, book=book,
        borrow_date=today,
        expected_return_date=today + timedelta(days=2),
        actual_return_date=None
    )
    Borrowing.objects.create(
        user=u, book=book,
        borrow_date=today - timedelta(days=7),
        expected_return_date=today - timedelta(days=3),
        actual_return_date=today - timedelta(days=1)
    )

    c = APIClient(); c.force_authenticate(user=u)
    r_true = c.get("/api/borrowings/?overdue=true")
    r_false = c.get("/api/borrowings/?overdue=false")

    assert r_true.status_code == 200 and len(r_true.json()) == 1
    assert r_false.status_code == 200 and len(r_false.json()) == 2  # дві не-overdue (активна й повернена)

@pytest.mark.django_db
def test_admin_can_return_others_borrowing():
    U = get_user_model()
    admin = U.objects.create(email="a@example.com", is_staff=True); admin.set_password("x"); admin.save()
    owner = U.objects.create(email="u@example.com"); owner.set_password("x"); owner.save()
    book = Book.objects.create(title="A", author="B", cover="HARD", inventory=0, daily_fee="1.00")

    today = date.today()
    br = Borrowing.objects.create(
        user=owner, book=book,
        borrow_date=today - timedelta(days=2),
        expected_return_date=today - timedelta(days=1),
        actual_return_date=None
    )

    c = APIClient(); c.force_authenticate(user=admin)
    r = c.post(f"/api/borrowings/{br.id}/return/")
    assert r.status_code == 200
    book.refresh_from_db()
    assert book.inventory == 1
    assert r.json()["actual_return_date"] is not None
