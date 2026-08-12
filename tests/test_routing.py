def _make_node(client, headers, lat, lng):
    r = client.post("/api/sidewalks/nodes", json={"latitude": lat, "longitude": lng}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_edge(client, headers, a_id, b_id):
    r = client.post("/api/sidewalks/edges", json={"node_a_id": a_id, "node_b_id": b_id}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _request_route(client, headers, origin, dest):
    r = client.post("/api/navigation/route", json={
        "origin_lat": origin[0], "origin_lng": origin[1],
        "destination_lat": dest[0], "destination_lng": dest[1],
    }, headers=headers)
    return r


def test_route_stable_near_edge_midpoint(client, admin_headers, register_user):
    a = (10.0000, -84.5000)
    b = (10.0000, -84.4990)
    c = (10.0010, -84.4990)

    a_id = _make_node(client, admin_headers, *a)
    b_id = _make_node(client, admin_headers, *b)
    c_id = _make_node(client, admin_headers, *c)
    _make_edge(client, admin_headers, a_id, b_id)
    _make_edge(client, admin_headers, b_id, c_id)

    user_headers, _, _ = register_user(prefix="router")

    mid_lat = (a[0] + b[0]) / 2
    mid_lng = (a[1] + b[1]) / 2
    nudge = 0.00002

    r_left = _request_route(client, user_headers, (mid_lat - nudge, mid_lng), c)
    r_right = _request_route(client, user_headers, (mid_lat + nudge, mid_lng), c)
    assert r_left.status_code == 201, r_left.text
    assert r_right.status_code == 201, r_right.text

    diff = abs(r_left.json()["distance_m"] - r_right.json()["distance_m"])
    assert diff < 5, f"la ruta sigue siendo inestable ante ruido chico de GPS: {diff}m de diferencia"


def test_route_direct_when_same_edge(client, admin_headers, register_user):
    a = (10.0100, -84.5100)
    b = (10.0100, -84.5090)

    a_id = _make_node(client, admin_headers, *a)
    b_id = _make_node(client, admin_headers, *b)
    _make_edge(client, admin_headers, a_id, b_id)

    user_headers, _, _ = register_user(prefix="router")

    near_b = (b[0], b[1] - 0.00003)
    r = _request_route(client, user_headers, near_b, b)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["distance_m"] < 25
    assert len(data["points"]) <= 3


def test_no_route_without_nearby_sidewalks(client, register_user):
    user_headers, _, _ = register_user(prefix="router")
    far_away = (1.0000, -70.0000)
    r = _request_route(client, user_headers, far_away, (1.0010, -70.0010))
    assert r.status_code == 422


def test_route_generates_turn_instruction(client, admin_headers, register_user):
    a = (10.0200, -84.5200)
    b = (10.0200, -84.5190)
    c = (10.0190, -84.5190)

    a_id = _make_node(client, admin_headers, *a)
    b_id = _make_node(client, admin_headers, *b)
    c_id = _make_node(client, admin_headers, *c)
    _make_edge(client, admin_headers, a_id, b_id)
    _make_edge(client, admin_headers, b_id, c_id)

    user_headers, _, _ = register_user(prefix="router")
    r = _request_route(client, user_headers, a, c)
    assert r.status_code == 201, r.text
    steps = r.json()["steps"]

    turns = [s["turn"] for s in steps if s["turn"] in ("left", "right")]
    assert turns, f"se esperaba al menos un giro anunciado, steps={steps}"
    assert turns[0] == "right"
