import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import db


class FakeCursor:
    def __init__(self):
        self.executed = []  # list of (sql, params)
        self.fetch_result = []
        self.fetchone_result = None
        self.fetchone_queue = []  # if set, fetchone() pops these in order first

    def execute(self, sql, *params):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.fetch_result

    def fetchone(self):
        if self.fetchone_queue:
            return self.fetchone_queue.pop(0)
        return self.fetchone_result


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
        "user_id": 1,
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
    # user_id + 17 columns -> 18 bound params
    assert len(params) == 18
    assert params[0] == 1
    assert params[1] == "en"
    assert params[-2] == "system"


def test_insert_event_defaults_when_fields_missing():
    conn = FakeConnection()
    db.insert_event(conn, {"raw_description": "x", "extract_fact": "y"})

    sql, params = conn._cursor.executed[0]
    assert params[0] is None  # no user_id supplied
    assert params[1] == "en"  # default language
    assert params[2] == "Unreasonable situation"  # default source_label
    assert params[-2] == "archive"  # default destination_tag


def test_get_total_counts_returns_rows():
    conn = FakeConnection()
    conn._cursor.fetch_result = [("system", 3, "2026-01-01", "2026-01-10")]
    rows = db.get_total_counts(conn, 1)
    assert rows == [("system", 3, "2026-01-01", "2026-01-10")]
    sql, params = conn._cursor.executed[0]
    assert "WHERE user_id = ?" in sql
    assert params == (1,)


def test_get_weekly_counts_returns_rows():
    conn = FakeConnection()
    conn._cursor.fetch_result = [(2026, 2, "archive", 1)]
    rows = db.get_weekly_counts(conn, 1)
    assert rows == [(2026, 2, "archive", 1)]
    sql, params = conn._cursor.executed[0]
    assert "WHERE user_id = ?" in sql
    assert params == (1,)


def test_create_user_hashes_password_and_returns_id():
    conn = FakeConnection()
    conn._cursor.fetchone_result = (42,)
    user_id = db.create_user(conn, "nevra@example.com", "supersecret")

    assert user_id == 42
    assert conn.committed is True
    sql, params = conn._cursor.executed[0]
    assert "INSERT INTO dbo.users" in sql
    assert params[0] == "nevra@example.com"
    assert params[1] != "supersecret"  # stored as a hash, not plaintext


def test_get_user_by_email_returns_row():
    conn = FakeConnection()
    conn._cursor.fetchone_result = (1, "nevra@example.com", "hashed")
    row = db.get_user_by_email(conn, "nevra@example.com")
    assert row == (1, "nevra@example.com", "hashed")


def test_verify_password_roundtrip():
    conn = FakeConnection()
    conn._cursor.fetchone_result = (1,)
    db.create_user(conn, "a@example.com", "supersecret")
    _, params = conn._cursor.executed[0]
    password_hash = params[1]

    assert db.verify_password(password_hash, "supersecret") is True
    assert db.verify_password(password_hash, "wrongpassword") is False


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
