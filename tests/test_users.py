import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_register_token_me_flow():
    c = APIClient()
    r = c.post("/users/", {"email":"t@example.com","password":"pass1234"}, format="json")
    assert r.status_code == 201
    tok = c.post("/users/token/", {"email":"t@example.com","password":"pass1234"}, format="json").json()
    c.credentials(HTTP_AUTHORIZE=f"Bearer {tok['access']}")
    me = c.get("/users/me/")
    assert me.status_code == 200
    assert me.json()["email"] == "t@example.com"
