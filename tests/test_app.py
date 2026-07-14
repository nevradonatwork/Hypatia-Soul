import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import app as app_module
import db
from test_db import FakeConnection


@pytest.fixture
def client(monkeypatch):
    fake_conn = FakeConnection()
    monkeypatch.setattr(db, "get_connection", lambda: fake_conn)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        c.fake_conn = fake_conn
        yield c


def test_index_page_loads_english_by_default(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Trigger tracker" in resp.data


def test_index_page_loads_turkish(client):
    resp = client.get("/?lang=tr")
    assert resp.status_code == 200
    assert "Tetikleyici takip".encode("utf-8") in resp.data


def test_submit_missing_required_fields_returns_400(client):
    resp = client.post("/submit", data={"raw_description": ""})
    assert resp.status_code == 400
    assert len(client.fake_conn._cursor.executed) == 0


def test_submit_valid_event_saves_and_redirects(client):
    resp = client.post("/submit", data={
        "raw_description": "he withheld the passport",
        "extract_fact": "passport not handed over on agreed date",
        "transform_intensity_score": "8",
        "transform_signal_type": "action_needed",
    })
    assert resp.status_code == 302
    assert "/counts" in resp.headers["Location"]
    assert len(client.fake_conn._cursor.executed) == 1
    assert client.fake_conn.committed is True


def test_submit_auto_suggests_destination_when_not_overridden(client):
    client.post("/submit", data={
        "raw_description": "he cancelled last minute again",
        "extract_fact": "cancelled pickup with no notice",
        "transform_signal_type": "needs_processing",
    })
    _, params = client.fake_conn._cursor.executed[0]
    assert params[-2] == "archive"  # needs_processing -> archive


def test_submit_manual_override_wins_over_suggestion(client):
    client.post("/submit", data={
        "raw_description": "he cancelled last minute again",
        "extract_fact": "cancelled pickup with no notice",
        "transform_signal_type": "needs_processing",
        "destination_tag": "system",
    })
    _, params = client.fake_conn._cursor.executed[0]
    assert params[-2] == "system"  # manual override wins


def test_counts_page_renders_totals_and_weekly(client):
    client.fake_conn._cursor.fetch_result = [("system", 2, "2026-01-01", "2026-01-05")]
    resp = client.get("/counts")
    assert resp.status_code == 200
    assert b"system" in resp.data


def test_submit_unsure_and_unanswered_yes_no_fields_store_null(client):
    client.post("/submit", data={
        "raw_description": "he cancelled last minute again",
        "extract_fact": "cancelled pickup with no notice",
        "transform_signal_type": "needs_processing",
        "extract_is_evidence_based": "unsure",
        # filter_feels_familiar intentionally omitted (not answered)
    })
    _, params = client.fake_conn._cursor.executed[0]
    # column order: language, source_label, raw_description, extract_fact,
    # extract_third_party_version, extract_is_evidence_based, extract_is_recurring_pattern, ...
    assert params[5] is None  # extract_is_evidence_based -> "unsure" maps to NULL
    assert params[11] is None  # filter_feels_familiar -> unanswered maps to NULL
