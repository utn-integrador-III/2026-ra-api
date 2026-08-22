def test_get_preferences_creates_defaults(client, register_user):
    headers, _, _ = register_user(prefix="prefdefault")
    r = client.get("/api/preferences", headers=headers)
    assert r.status_code == 200
    assert r.json()["voice_guidance_enabled"] is True
    assert r.json()["walking_speed_mps"] == 1.3


def test_update_preferences_partial(client, register_user):
    headers, _, _ = register_user(prefix="prefupdate")
    client.get("/api/preferences", headers=headers)

    r = client.put("/api/preferences", json={"voice_guidance_enabled": False}, headers=headers)
    assert r.status_code == 200
    assert r.json()["voice_guidance_enabled"] is False
    assert r.json()["walking_speed_mps"] == 1.3

    r2 = client.put("/api/preferences", json={"walking_speed_mps": 1.0}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["voice_guidance_enabled"] is False
    assert r2.json()["walking_speed_mps"] == 1.0


def test_preferences_require_auth(client):
    r = client.get("/api/preferences")
    assert r.status_code in (401, 403)
