def _make_node(client, headers, lat, lng):
    r = client.post("/api/sidewalks/nodes", json={"latitude": lat, "longitude": lng}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_edge(client, headers, a_id, b_id):
    r = client.post("/api/sidewalks/edges", json={"node_a_id": a_id, "node_b_id": b_id}, headers=headers)
    assert r.status_code == 201, r.text


def _make_route(client, admin_headers, user_headers, base_lat=10.0300, base_lng=-84.5300):
    a_id = _make_node(client, admin_headers, base_lat, base_lng)
    b_id = _make_node(client, admin_headers, base_lat, base_lng + 0.0010)
    _make_edge(client, admin_headers, a_id, b_id)

    r = client.post("/api/navigation/route", json={
        "origin_lat": base_lat, "origin_lng": base_lng,
        "destination_lat": base_lat, "destination_lng": base_lng + 0.0010,
    }, headers=user_headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_start_finish_and_get_route(client, admin_headers, register_user):
    user_headers, _, _ = register_user(prefix="navlifecycle")
    route = _make_route(client, admin_headers, user_headers)

    started = client.post("/api/navigation/start", json={"route_id": route["id"]}, headers=user_headers)
    assert started.status_code == 200
    assert started.json()["status"] == "active"

    finished = client.post("/api/navigation/finish", json={"route_id": route["id"]}, headers=user_headers)
    assert finished.status_code == 200
    assert finished.json()["status"] == "finished"

    got = client.get(f"/api/navigation/{route['id']}", headers=user_headers)
    assert got.status_code == 200
    assert got.json()["id"] == route["id"]


def test_recalculate_route(client, admin_headers, register_user):
    user_headers, _, _ = register_user(prefix="navrecalc")
    route = _make_route(client, admin_headers, user_headers, base_lat=10.0400, base_lng=-84.5400)

    r = client.post("/api/navigation/recalculate", json={
        "route_id": route["id"], "current_lat": 10.0400, "current_lng": -84.5400,
    }, headers=user_headers)
    assert r.status_code == 200
    assert r.json()["id"] == route["id"]


def test_history_lists_users_routes(client, admin_headers, register_user):
    user_headers, _, _ = register_user(prefix="navhistory")
    route = _make_route(client, admin_headers, user_headers, base_lat=10.0500, base_lng=-84.5500)

    r = client.get("/api/navigation/history", headers=user_headers)
    assert r.status_code == 200
    assert any(item["id"] == route["id"] for item in r.json())


def test_delete_route(client, admin_headers, register_user):
    user_headers, _, _ = register_user(prefix="navdelete")
    route = _make_route(client, admin_headers, user_headers, base_lat=10.0600, base_lng=-84.5600)

    r = client.delete(f"/api/navigation/{route['id']}", headers=user_headers)
    assert r.status_code == 204

    got = client.get(f"/api/navigation/{route['id']}", headers=user_headers)
    assert got.status_code == 404


def test_route_not_owned_by_another_user_is_forbidden(client, admin_headers, register_user):
    owner_headers, _, _ = register_user(prefix="navowner")
    route = _make_route(client, admin_headers, owner_headers, base_lat=10.0700, base_lng=-84.5700)

    intruder_headers, _, _ = register_user(prefix="navintruder")
    r = client.get(f"/api/navigation/{route['id']}", headers=intruder_headers)
    assert r.status_code == 403


def test_unknown_route_is_404(client, register_user):
    headers, _, _ = register_user(prefix="navmissing")
    r = client.get("/api/navigation/no-existe", headers=headers)
    assert r.status_code == 404
