import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_non_admin_cannot_create_book():
    User = get_user_model()
    user = User.objects.create(email="u@example.com")
    user.set_password("x"); user.save()

    c = APIClient()
    c.force_authenticate(user=user)
    payload = {"title":"A","author":"B","cover":"HARD","inventory":1,"daily_fee":"1.00"}
    r = c.post("/api/books/", payload, format="json")
    assert r.status_code in (401, 403)
