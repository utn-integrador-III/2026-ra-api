def _make_node(client, headers, lat, lng):
    r = client.post("/api/sidewalks/nodes", json={"latitude": lat, "longitude": lng}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_non_admin_cannot_create_node(client, register_user):
    headers, _, _ = register_user(prefix="plain")
    r = client.post("/api/sidewalks/nodes", json={"latitude": 9.93, "longitude": -84.08}, headers=headers)
    assert r.status_code == 403


def test_admin_can_create_node_and_edge(client, admin_headers):
    a = _make_node(client, admin_headers, 9.9300, -84.0800)
    b = _make_node(client, admin_headers, 9.9301, -84.0800)

    r = client.post("/api/sidewalks/edges", json={"node_a_id": a, "node_b_id": b}, headers=admin_headers)
    assert r.status_code == 201, r.text
    edge = r.json()
    assert edge["node_a_id"] == a
    assert edge["node_b_id"] == b
    assert edge["distance_m"] > 0


def test_reject_self_edge(client, admin_headers):
    a = _make_node(client, admin_headers, 9.9310, -84.0810)
    r = client.post("/api/sidewalks/edges", json={"node_a_id": a, "node_b_id": a}, headers=admin_headers)
    assert r.status_code == 400


def test_reject_duplicate_edge(client, admin_headers):
    a = _make_node(client, admin_headers, 9.9320, -84.0820)
    b = _make_node(client, admin_headers, 9.9321, -84.0820)
    r1 = client.post("/api/sidewalks/edges", json={"node_a_id": a, "node_b_id": b}, headers=admin_headers)
    assert r1.status_code == 201

    r2 = client.post("/api/sidewalks/edges", json={"node_a_id": b, "node_b_id": a}, headers=admin_headers)
    assert r2.status_code == 409


def test_delete_node_cascades_edges(client, admin_headers):
    a = _make_node(client, admin_headers, 9.9330, -84.0830)
    b = _make_node(client, admin_headers, 9.9331, -84.0830)
    edge = client.post("/api/sidewalks/edges", json={"node_a_id": a, "node_b_id": b}, headers=admin_headers).json()

    del_r = client.delete(f"/api/sidewalks/nodes/{a}", headers=admin_headers)
    assert del_r.status_code == 204

    edges = client.get("/api/sidewalks/edges", headers=admin_headers).json()
    assert all(e["id"] != edge["id"] for e in edges)


def test_list_nodes(client, admin_headers):
    node_id = _make_node(client, admin_headers, 9.9340, -84.0840)
    r = client.get("/api/sidewalks/nodes", headers=admin_headers)
    assert r.status_code == 200
    assert any(n["id"] == node_id for n in r.json())


def test_delete_unknown_node_404(client, admin_headers):
    r = client.delete("/api/sidewalks/nodes/no-existe", headers=admin_headers)
    assert r.status_code == 404


def test_create_edge_unknown_node_404(client, admin_headers):
    a = _make_node(client, admin_headers, 9.9350, -84.0850)
    r = client.post("/api/sidewalks/edges", json={"node_a_id": a, "node_b_id": "no-existe"}, headers=admin_headers)
    assert r.status_code == 404


def test_delete_edge_success_and_unknown_404(client, admin_headers):
    a = _make_node(client, admin_headers, 9.9360, -84.0860)
    b = _make_node(client, admin_headers, 9.9361, -84.0860)
    edge = client.post("/api/sidewalks/edges", json={"node_a_id": a, "node_b_id": b}, headers=admin_headers).json()

    r = client.delete(f"/api/sidewalks/edges/{edge['id']}", headers=admin_headers)
    assert r.status_code == 204

    r2 = client.delete("/api/sidewalks/edges/no-existe", headers=admin_headers)
    assert r2.status_code == 404
