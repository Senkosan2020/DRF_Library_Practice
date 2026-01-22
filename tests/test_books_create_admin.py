import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_admin_can_create_book():
    User = get_user_model()
    admin = User.objects.create(email="a@example.com", is_staff=True)
    admin.set_password("x"); admin.save()

    c = APIClient()
    c.force_authenticate(user=admin)
    payload = {"title":"A","author":"B","cover":"HARD","inventory":2,"daily_fee":"2.50"}
    r = c.post("/api/books/", payload, format="json")
    assert r.status_code == 201
