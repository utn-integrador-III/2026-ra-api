from datetime import datetime, timedelta, timezone

from app.api.history_router import _time_ago


def test_time_ago_ranges():
    now = datetime.now(timezone.utc)
    assert _time_ago(now) == "Ahora"
    assert _time_ago(now - timedelta(minutes=5)) == "Hace 5min"
    assert _time_ago(now - timedelta(hours=3)) == "Hace 3h"
    assert _time_ago(now - timedelta(hours=30)) == "Ayer"
    assert _time_ago(now - timedelta(days=5)) == "Hace 5d"


def test_add_and_list_places(client, register_user):
    headers, _, _ = register_user(prefix="histplaces")

    r = client.post("/api/history/places", json={
        "name": "Biblioteca", "address": "Edificio A", "latitude": 9.93, "longitude": -84.08, "type": "library",
    }, headers=headers)
    assert r.status_code == 201
    assert r.json()["message"] == "Agregado a recientes"

    r2 = client.get("/api/history/places", headers=headers)
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] == 1
    assert data["places"][0]["name"] == "Biblioteca"
    assert "time_ago" in data["places"][0]


def test_add_same_place_twice_updates_instead_of_duplicating(client, register_user):
    headers, _, _ = register_user(prefix="histdup")
    body = {"name": "Cafeteria", "address": "Edificio B", "latitude": 9.93, "longitude": -84.08, "type": "food"}

    r1 = client.post("/api/history/places", json=body, headers=headers)
    assert r1.json()["message"] == "Agregado a recientes"

    r2 = client.post("/api/history/places", json=body, headers=headers)
    assert r2.json()["message"] == "Actualizado en recientes"

    places = client.get("/api/history/places", headers=headers).json()["places"]
    assert len([p for p in places if p["name"] == "Cafeteria"]) == 1


def test_clear_history(client, register_user):
    headers, _, _ = register_user(prefix="histclear")
    client.post("/api/history/places", json={"name": "Lugar"}, headers=headers)

    r = client.delete("/api/history/places", headers=headers)
    assert r.status_code == 200

    places = client.get("/api/history/places", headers=headers).json()["places"]
    assert places == []
