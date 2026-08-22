from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("miClave123")
    assert hashed != "miClave123"
    assert verify_password("miClave123", hashed)
    assert not verify_password("otraClave", hashed)


def test_create_and_decode_token_roundtrip():
    token = create_access_token({"sub": "user-1", "email": "a@b.com"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["email"] == "a@b.com"


def test_decode_invalid_token_returns_none():
    assert decode_access_token("esto-no-es-un-jwt-valido") is None
