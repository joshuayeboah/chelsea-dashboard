"""
Smoke test: does the app actually import and start, and do the core
endpoints respond. This exists so a broken import or a crashing startup
can never reach production undetected — currently the only thing standing
between a bad commit and an auto-deploy is this test.

Seeds the database directly (local, no network) before the TestClient
starts the app, so FastAPI's lifespan sees a non-empty roster and skips
the live API-Football scrape — this test must stay network-independent.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import init_db, get_all_players  # noqa: E402
from seed import seed  # noqa: E402


def _ensure_seeded():
    init_db()
    if not get_all_players():
        seed()


def test_app_starts_and_serves_core_endpoints():
    _ensure_seeded()

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as client:
        r = client.get("/")
        assert r.status_code == 200

        r = client.get("/transfers")
        assert r.status_code == 200
        body = r.json()
        assert "transfers" in body and "count" in body
        assert body["count"] == len(body["transfers"])
        assert body["count"] > 0

        r = client.get("/metrics/summary")
        assert r.status_code == 200

        r = client.get("/metrics/value-quadrants")
        assert r.status_code == 200

        r = client.get("/seasons")
        assert r.status_code == 200

        r = client.get("/scrape/status")
        assert r.status_code == 200
