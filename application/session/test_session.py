from fastapi import responses
from fastapi.testclient import TestClient 

from ..factory import create_app

app  = create_app()
client = TestClient(app)


def test_signup():
    data = {"first_name": "Judita", "last_name": "Lumnwi", "email": "gloxonempire@gmail.com", "password": 123456}
    response = client.post("v1/auth/signup", json=data)
    assert response.status_code == 200 
    assert response.json().get("data").get("first_name") == "Judita"


def test_email_already_exist():
    data = {"first_name": "Judita", "last_name": "Lumnwi", "email": "gloxonempire@gmail.com", "password": 123456}
    response = client.post("v1/auth/signup", json=data)
    assert response.status_code == 409 
