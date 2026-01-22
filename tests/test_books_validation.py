import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

@pytest.fixture
def admin_client(db):
    User = get_user_model()
    admin = User.objects.create(email="admin@example.com", is_staff=True)
    admin.set_password("x"); admin.save()
    c = APIClient()
    c.force_authenticate(user=admin)
    return c

def test_inventory_must_be_positive(admin_client):
    r = admin_client.post("/api/books/", {"title":"A","author":"B","cover":"HARD","inventory":0,"daily_fee":"1.00"}, format="json")
    assert r.status_code == 400
    assert "inventory" in r.json()

def test_daily_fee_must_be_positive(admin_client):
    r = admin_client.post("/api/books/", {"title":"A","author":"B","cover":"HARD","inventory":1,"daily_fee":"0.00"}, format="json")
    assert r.status_code == 400
    assert "daily_fee" in r.json()
