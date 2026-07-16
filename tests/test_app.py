import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import app as app_module
import db
from test_db import FakeConnection


@pytest.fixture
def anon_client(monkeypatch):
    """A test client with no logged-in user."""
    fake_conn = FakeConnection()
    monkeypatch.setattr(db, "get_connection", lambda: fake_conn)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        c.fake_conn = fake_conn
        yield c


@pytest.fixture
def client(anon_client):
    """A test client with a fake logged-in user (user_id=1)."""
    with anon_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["email"] = "nevra@example.com"
    return anon_client


def test_index_requires_login(anon_client):
    resp = anon_client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_submit_requires_login(anon_client):
    resp = anon_client.post("/submit", data={"raw_description": "x"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_counts_requires_login(anon_client):
    resp = anon_client.get("/counts")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_register_creates_user_and_logs_in(anon_client):
    # first fetchone(): get_user_by_email -> no existing user; second: create_user's new id
    anon_client.fake_conn._cursor.fetchone_queue = [None, (5,)]
    resp = anon_client.post("/register", data={"email": "new@example.com", "password": "supersecret"})
    assert resp.status_code == 302
    assert "/" in resp.headers["Location"]
    with anon_client.session_transaction() as sess:
        assert sess["user_id"] is not None
        assert sess["email"] == "new@example.com"


def test_register_rejects_short_password(anon_client):
    resp = anon_client.post("/register", data={"email": "new@example.com", "password": "short"})
    assert resp.status_code == 400
    with anon_client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_succeeds_with_correct_password(anon_client):
    from werkzeug.security import generate_password_hash
    anon_client.fake_conn._cursor.fetchone_result = (7, "nevra@example.com", generate_password_hash("supersecret"))

    resp = anon_client.post("/login", data={"email": "nevra@example.com", "password": "supersecret"})
    assert resp.status_code == 302
    with anon_client.session_transaction() as sess:
        assert sess["user_id"] == 7


def test_login_fails_with_wrong_password(anon_client):
    from werkzeug.security import generate_password_hash
    anon_client.fake_conn._cursor.fetchone_result = (7, "nevra@example.com", generate_password_hash("supersecret"))

    resp = anon_client.post("/login", data={"email": "nevra@example.com", "password": "wrong"})
    assert resp.status_code == 401
    with anon_client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_clears_session(client):
    resp = client.get("/logout")
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert "user_id" not in sess


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
    # column order: user_id, language, source_label, raw_description, extract_fact,
    # extract_third_party_version, extract_is_evidence_based, extract_is_recurring_pattern, ...
    assert params[6] is None  # extract_is_evidence_based -> "unsure" maps to NULL
    assert params[12] is None  # filter_feels_familiar -> unanswered maps to NULL
