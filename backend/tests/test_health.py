from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}
