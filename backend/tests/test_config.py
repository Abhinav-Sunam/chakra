from starlette.testclient import TestClient
from app.main import app

def test_config_endpoints():
    """Test GET /api/config and POST /api/config endpoints."""
    with TestClient(app) as client:
        res = client.get("/api/config")
        assert res.status_code == 200
        cfg = res.json()
        assert "constellation" in cfg
        assert cfg["constellation"]["T"] == 120

        # Partial update
        update_res = client.post("/api/config", json={"sim": {"time_scale": 30.0}})
        assert update_res.status_code == 200
        data = update_res.json()
        assert data["ok"] is True
        assert data["config"]["sim"]["time_scale"] == 30.0

        # Verify updated
        get_res = client.get("/api/config")
        assert get_res.json()["sim"]["time_scale"] == 30.0

