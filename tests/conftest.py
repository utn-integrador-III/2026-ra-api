import json
import os
import tempfile
import uuid

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(tempfile.gettempdir(), "pathar_test_unused.db"),
)
os.environ.setdefault("JWT_SECRET_KEY", "clave-de-pruebas-no-usar-en-produccion")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")

_dummy_creds_path = os.path.join(tempfile.gettempdir(), "pathar_test_firebase_creds.json")
if not os.path.exists(_dummy_creds_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    _key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _pem = _key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    with open(_dummy_creds_path, "w") as f:
        json.dump({
            "type": "service_account",
            "project_id": "pathar-test",
            "private_key_id": "0" * 40,
            "private_key": _pem,
            "client_email": "test@pathar-test.iam.gserviceaccount.com",
            "client_id": "0" * 21,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40pathar-test.iam.gserviceaccount.com",
        }, f)
os.environ.setdefault("FIREBASE_CREDENTIALS_PATH", _dummy_creds_path)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as main_module
from app.database.database import Base, get_db
from app.models.user_model import User

_TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"pathar_test_{uuid.uuid4().hex}.db")
_test_engine = create_engine(f"sqlite:///{_TEST_DB_PATH}", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
Base.metadata.create_all(bind=_test_engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


main_module.app.dependency_overrides[get_db] = _override_get_db


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture(scope="session")
def client():
    return TestClient(main_module.app)


@pytest.fixture
def register_user(client):
    def _register(prefix: str = "user", password: str = "123456"):
        email = unique_email(prefix)
        r = client.post("/api/auth/register", json={
            "name": prefix.capitalize(), "email": email, "password": password,
        })
        assert r.status_code == 201, r.text
        data = r.json()
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        return headers, data["user"]["id"], email

    return _register


@pytest.fixture
def admin_headers(register_user):
    headers, user_id, _ = register_user(prefix="admin")
    db = TestSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.role = "admin"
        db.commit()
    finally:
        db.close()
    return headers
