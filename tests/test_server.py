# tests/test_server.py
from fastapi.testclient import TestClient
from server.mcp_server import app

client = TestClient(app)

def test_manifest():
    r = client.get("/mcp/manifest")
    assert r.status_code == 200
    data = r.json()
    assert "tools" in data

def test_flights_list():
    r = client.get("/mcp/tool/flights.list?region=region1")
    assert r.status_code == 200
    data = r.json()
    assert "flights" in data

def test_flights_get_not_found():
    r = client.get("/mcp/tool/flights.get?identifier=NONEXISTENT123")
    assert r.status_code == 404
