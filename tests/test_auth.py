from unittest.mock import patch

from tests.conftest import TestSessionLocal, unique_email
from app.models.user_model import User


def test_register_success(client):
    email = unique_email("register")
    r = client.post("/api/auth/register", json={
        "name": "Nueva Persona", "email": email, "password": "123456",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["access_token"]
    assert data["user"]["email"] == email
    assert data["user"]["auth_provider"] == "local"


def test_register_duplicate_email_rejected(client):
    email = unique_email("dup")
    body = {"name": "Persona", "email": email, "password": "123456"}
    r1 = client.post("/api/auth/register", json=body)
    assert r1.status_code == 201

    r2 = client.post("/api/auth/register", json=body)
    assert r2.status_code == 400


def test_register_short_password_rejected(client):
    r = client.post("/api/auth/register", json={
        "name": "Persona", "email": unique_email("short"), "password": "123",
    })
    assert r.status_code == 400


def test_login_success(client):
    email = unique_email("login")
    password = "unaClaveSegura"
    client.post("/api/auth/register", json={"name": "Persona", "email": email, "password": password})

    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password_rejected(client):
    email = unique_email("wrongpass")
    client.post("/api/auth/register", json={"name": "Persona", "email": email, "password": "123456"})

    r = client.post("/api/auth/login", json={"email": email, "password": "otra-clave"})
    assert r.status_code == 401


def test_login_unknown_email_rejected(client):
    r = client.post("/api/auth/login", json={"email": unique_email("nunca"), "password": "123456"})
    assert r.status_code == 401


def test_profile_requires_token(client):
    r = client.get("/api/auth/profile")
    assert r.status_code in (401, 403)


def test_profile_with_token(client, register_user):
    headers, _, email = register_user(prefix="profile")
    r = client.get("/api/auth/profile", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_profile_with_garbage_token_rejected(client):
    r = client.get("/api/auth/profile", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401


def test_login_inactive_account_rejected(client, register_user):
    headers, user_id, email = register_user(prefix="inactive")
    db = TestSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.is_active = False
        db.commit()
    finally:
        db.close()

    r = client.post("/api/auth/login", json={"email": email, "password": "123456"})
    assert r.status_code == 403


def test_google_auth_invalid_token_rejected(client):
    with patch("app.api.auth_router.firebase_auth.verify_id_token", side_effect=Exception("bad token")):
        r = client.post("/api/auth/google", json={"id_token": "cualquiera"})
    assert r.status_code == 401


def test_google_auth_creates_new_user(client):
    decoded = {"uid": "google-uid-nuevo", "email": unique_email("googlenuevo"), "name": "Persona Google"}
    with patch("app.api.auth_router.firebase_auth.verify_id_token", return_value=decoded):
        r = client.post("/api/auth/google", json={"id_token": "token-valido"})
    assert r.status_code == 200
    assert r.json()["user"]["email"] == decoded["email"]
    assert r.json()["user"]["auth_provider"] == "google"


def test_google_auth_links_existing_local_account(client):
    email = unique_email("googlelink")
    client.post("/api/auth/register", json={"name": "Local", "email": email, "password": "123456"})

    decoded = {"uid": "google-uid-link", "email": email, "name": "Local"}
    with patch("app.api.auth_router.firebase_auth.verify_id_token", return_value=decoded):
        r = client.post("/api/auth/google", json={"id_token": "token-valido"})
    assert r.status_code == 200
    assert r.json()["user"]["auth_provider"] == "google"


def test_google_auth_existing_google_user_logs_in_again(client):
    decoded = {"uid": "google-uid-repeat", "email": unique_email("googlerepeat"), "name": "Repetido"}
    with patch("app.api.auth_router.firebase_auth.verify_id_token", return_value=decoded):
        first = client.post("/api/auth/google", json={"id_token": "token-valido"})
        second = client.post("/api/auth/google", json={"id_token": "token-valido"})
    assert first.json()["user"]["id"] == second.json()["user"]["id"]
