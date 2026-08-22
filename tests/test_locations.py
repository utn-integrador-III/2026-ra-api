def _make_location(client, headers, **overrides):
    body = {
        "name": "Aula 101", "description": "Salon principal", "location_type": "classroom",
        "latitude": 9.9300, "longitude": -84.0800, "building": "Edificio A", "floor": "1",
    }
    body.update(overrides)
    r = client.post("/api/locations/", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_non_admin_cannot_create_location(client, register_user):
    headers, _, _ = register_user(prefix="locplain")
    r = client.post("/api/locations/", json={
        "name": "X", "latitude": 9.93, "longitude": -84.08,
    }, headers=headers)
    assert r.status_code == 403


def test_create_list_get_update_delete_location(client, admin_headers, register_user):
    loc = _make_location(client, admin_headers, name="Laboratorio 5")
    loc_id = loc["id"]

    user_headers, _, _ = register_user(prefix="locreader")

    listed = client.get("/api/locations/", headers=user_headers).json()
    assert any(l["id"] == loc_id for l in listed)

    got = client.get(f"/api/locations/{loc_id}", headers=user_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Laboratorio 5"

    updated = client.put(f"/api/locations/{loc_id}", json={"name": "Laboratorio 5B"}, headers=admin_headers)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Laboratorio 5B"

    deleted = client.delete(f"/api/locations/{loc_id}", headers=admin_headers)
    assert deleted.status_code == 204

    after = client.get("/api/locations/", headers=user_headers).json()
    assert all(l["id"] != loc_id for l in after)


def test_get_unknown_location_404(client, register_user):
    headers, _, _ = register_user(prefix="locmissing")
    r = client.get("/api/locations/no-existe", headers=headers)
    assert r.status_code == 404


def test_list_with_search_and_type_filter(client, admin_headers, register_user):
    _make_location(client, admin_headers, name="Cafeteria Central", location_type="cafeteria")
    _make_location(client, admin_headers, name="Aula 202", location_type="classroom")

    user_headers, _, _ = register_user(prefix="locsearch")

    by_type = client.get("/api/locations/", params={"location_type": "cafeteria"}, headers=user_headers).json()
    assert all(l["location_type"] == "cafeteria" for l in by_type)
    assert any(l["name"] == "Cafeteria Central" for l in by_type)

    by_search = client.get("/api/locations/", params={"search": "202"}, headers=user_headers).json()
    assert any(l["name"] == "Aula 202" for l in by_search)


def test_list_with_coordinates_includes_distance(client, admin_headers, register_user):
    loc = _make_location(client, admin_headers, name="Punto Distancia", latitude=9.9400, longitude=-84.0900)
    user_headers, _, _ = register_user(prefix="locdist")

    r = client.get("/api/locations/", params={"lat": 9.9400, "lng": -84.0900}, headers=user_headers)
    found = next(l for l in r.json() if l["id"] == loc["id"])
    assert found["distance_m"] is not None
    assert found["distance_text"] is not None


def test_nearby_filters_by_radius(client, admin_headers, register_user):
    near = _make_location(client, admin_headers, name="Cerca", latitude=9.9500, longitude=-84.1000)
    far = _make_location(client, admin_headers, name="Lejos", latitude=10.5000, longitude=-85.0000)

    user_headers, _, _ = register_user(prefix="locnearby")
    r = client.get("/api/locations/nearby", params={"lat": 9.9500, "lng": -84.1000, "radius_m": 200}, headers=user_headers)
    ids = [l["id"] for l in r.json()]
    assert near["id"] in ids
    assert far["id"] not in ids
