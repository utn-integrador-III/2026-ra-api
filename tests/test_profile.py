def test_get_and_update_profile(client, register_user):
    headers, _, email = register_user(prefix="profileflow")
    r = client.get("/api/auth/profile", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert r.json()["auth_provider"] == "local"

    r2 = client.put("/api/auth/profile", json={"name": "Nombre Nuevo"}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["name"] == "Nombre Nuevo"


def test_favorites_stub_endpoints(client, register_user):
    headers, _, _ = register_user(prefix="fav")
    assert client.get("/api/favorites", headers=headers).json() == {"favorites": [], "total": 0}

    r = client.post("/api/favorites", json={
        "name": "Biblioteca", "address": "Edificio A", "latitude": 9.93, "longitude": -84.08,
    }, headers=headers)
    assert r.status_code == 201

    r2 = client.delete("/api/favorites/algun-id", headers=headers)
    assert r2.status_code == 200


def test_history_routes_stub(client, register_user):
    headers, _, _ = register_user(prefix="histroutes")
    r = client.get("/api/history/routes", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"routes": [], "total": 0}


def test_non_admin_cannot_list_users(client, register_user):
    headers, _, _ = register_user(prefix="plainlist")
    r = client.get("/api/admin/users", headers=headers)
    assert r.status_code == 403


def test_admin_can_list_and_change_role(client, admin_headers, register_user):
    _, other_user_id, other_email = register_user(prefix="tobepromoted")

    r = client.get("/api/admin/users", headers=admin_headers)
    assert r.status_code == 200
    assert any(u["email"] == other_email for u in r.json())

    r2 = client.put(f"/api/admin/users/{other_user_id}/role", params={"role": "admin"}, headers=admin_headers)
    assert r2.status_code == 200
    assert r2.json()["user_id"] == other_user_id


def test_change_role_invalid_value_rejected(client, admin_headers, register_user):
    _, other_user_id, _ = register_user(prefix="badrole")
    r = client.put(f"/api/admin/users/{other_user_id}/role", params={"role": "superadmin"}, headers=admin_headers)
    assert r.status_code == 400


def test_change_role_unknown_user_rejected(client, admin_headers):
    r = client.put("/api/admin/users/no-existe/role", params={"role": "admin"}, headers=admin_headers)
    assert r.status_code == 404
