from app.database.database import get_db


def test_root_endpoint(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_get_db_yields_a_working_session():
    gen = get_db()
    db = next(gen)
    assert db is not None
    gen.close()
