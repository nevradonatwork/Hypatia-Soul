import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import db


class FakeCursor:
    def __init__(self):
        self.executed = []  # list of (sql, params)
        self.fetch_result = []

    def execute(self, sql, *params):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.fetch_result


class FakeConnection:
    def __init__(self):
        self._cursor = FakeCursor()
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass


def sample_payload():
    return {
        "language": "en",
        "source_label": "Unreasonable situation",
        "raw_description": "he withheld the passport",
        "extract_fact": "passport not handed over on agreed date",
        "extract_third_party_version": "he did not comply with the custody agreement",
        "extract_is_evidence_based": True,
        "extract_is_recurring_pattern": True,
        "transform_intensity_score": "8",
        "transform_is_proportional": True,
        "transform_signal_type": "action_needed",
        "transform_serves_purpose": True,
        "filter_feels_familiar": False,
        "filter_reaction_vs_event_size": "equal",
        "filter_would_react_same_stranger": True,
        "filter_echoes_childhood": False,
        "destination_tag": "system",
        "destination_note": "sent to solicitor",
    }


def test_insert_event_executes_and_commits():
    conn = FakeConnection()
    db.insert_event(conn, sample_payload())

    assert conn.committed is True
    assert len(conn._cursor.executed) == 1
    sql, params = conn._cursor.executed[0]
    assert "INSERT INTO dbo.events" in sql
    # 17 columns -> 17 bound params
    assert len(params) == 17
    assert params[0] == "en"
    assert params[-2] == "system"


def test_insert_event_defaults_when_fields_missing():
    conn = FakeConnection()
    db.insert_event(conn, {"raw_description": "x", "extract_fact": "y"})

    sql, params = conn._cursor.executed[0]
    assert params[0] == "en"  # default language
    assert params[1] == "Unreasonable situation"  # default source_label
    assert params[-2] == "archive"  # default destination_tag


def test_get_total_counts_returns_rows():
    conn = FakeConnection()
    conn._cursor.fetch_result = [("system", 3, "2026-01-01", "2026-01-10")]
    rows = db.get_total_counts(conn)
    assert rows == [("system", 3, "2026-01-01", "2026-01-10")]


def test_get_weekly_counts_returns_rows():
    conn = FakeConnection()
    conn._cursor.fetch_result = [(2026, 2, "archive", 1)]
    rows = db.get_weekly_counts(conn)
    assert rows == [(2026, 2, "archive", 1)]


def test_get_connection_string_defaults_to_windows_auth(monkeypatch):
    monkeypatch.delenv("TT_DB_AUTH", raising=False)
    monkeypatch.delenv("TT_DB_USER", raising=False)
    monkeypatch.delenv("TT_DB_PASSWORD", raising=False)
    monkeypatch.setenv("TT_DB_SERVER", "NevraDonat\\SQLEXPRESS")
    conn_str = db.get_connection_string()
    assert "Trusted_Connection=yes" in conn_str
    assert "SERVER=NevraDonat\\SQLEXPRESS" in conn_str


def test_get_connection_string_raises_without_credentials_when_sql_auth(monkeypatch):
    monkeypatch.setenv("TT_DB_AUTH", "sql")
    monkeypatch.delenv("TT_DB_USER", raising=False)
    monkeypatch.delenv("TT_DB_PASSWORD", raising=False)
    try:
        db.get_connection_string()
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_get_connection_string_builds_with_sql_login(monkeypatch):
    monkeypatch.setenv("TT_DB_AUTH", "sql")
    monkeypatch.setenv("TT_DB_USER", "nevra")
    monkeypatch.setenv("TT_DB_PASSWORD", "secret")
    monkeypatch.setenv("TT_DB_SERVER", "localhost")
    monkeypatch.setenv("TT_DB_NAME", "TriggerTracker")
    conn_str = db.get_connection_string()
    assert "UID=nevra" in conn_str
    assert "PWD=secret" in conn_str
    assert "DATABASE=TriggerTracker" in conn_str
