"""Data layer. Connects to SQL Server via pyodbc using a SQL login.

Connection settings come from environment variables so credentials are
never hardcoded:

    TT_DB_SERVER    e.g. "localhost\\SQLEXPRESS" or "localhost,1433"
    TT_DB_NAME      e.g. "TriggerTracker"
    TT_DB_USER      SQL login username
    TT_DB_PASSWORD  SQL login password
    TT_DB_DRIVER    optional, defaults to "ODBC Driver 17 for SQL Server"
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv may not be installed; env vars can still be set another way
    pass

try:
    import pyodbc
except ImportError:  # pyodbc may not be installed in every environment (e.g. tests)
    pyodbc = None


def get_connection_string() -> str:
    server = os.environ.get("TT_DB_SERVER", "localhost")
    database = os.environ.get("TT_DB_NAME", "TriggerTracker")
    user = os.environ.get("TT_DB_USER")
    password = os.environ.get("TT_DB_PASSWORD")
    driver = os.environ.get("TT_DB_DRIVER", "ODBC Driver 17 for SQL Server")

    if not user or not password:
        raise RuntimeError(
            "TT_DB_USER and TT_DB_PASSWORD environment variables must be set "
            "(SQL login, not Windows Authentication)."
        )

    return (
        f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
        f"UID={user};PWD={password};TrustServerCertificate=yes;"
    )


def get_connection():
    if pyodbc is None:
        raise RuntimeError("pyodbc is not installed. Run: pip install pyodbc")
    return pyodbc.connect(get_connection_string())


INSERT_EVENT_SQL = """
INSERT INTO dbo.events (
    language, source_label, raw_description,
    extract_fact, extract_third_party_version, extract_is_evidence_based, extract_is_recurring_pattern,
    transform_intensity_score, transform_is_proportional, transform_signal_type, transform_serves_purpose,
    filter_feels_familiar, filter_reaction_vs_event_size, filter_would_react_same_stranger, filter_echoes_childhood,
    destination_tag, destination_note
) VALUES (
    ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?
);
"""


def insert_event(conn, payload: dict) -> None:
    """Insert one event row. `conn` is any DB-API 2.0 connection
    (real pyodbc connection in production, a fake one in tests)."""
    cursor = conn.cursor()
    cursor.execute(
        INSERT_EVENT_SQL,
        payload.get("language", "en"),
        payload.get("source_label", "Unreasonable situation"),
        payload.get("raw_description"),
        payload.get("extract_fact"),
        payload.get("extract_third_party_version"),
        payload.get("extract_is_evidence_based"),
        payload.get("extract_is_recurring_pattern"),
        payload.get("transform_intensity_score"),
        payload.get("transform_is_proportional"),
        payload.get("transform_signal_type"),
        payload.get("transform_serves_purpose"),
        payload.get("filter_feels_familiar"),
        payload.get("filter_reaction_vs_event_size"),
        payload.get("filter_would_react_same_stranger"),
        payload.get("filter_echoes_childhood"),
        payload.get("destination_tag", "archive"),
        payload.get("destination_note"),
    )
    conn.commit()


def get_total_counts(conn) -> list:
    """Returns rows: (destination_tag, trigger_count, first_event, last_event)."""
    cursor = conn.cursor()
    cursor.execute("SELECT destination_tag, trigger_count, first_event, last_event FROM dbo.v_trigger_counts_total;")
    return cursor.fetchall()


def get_weekly_counts(conn) -> list:
    """Returns rows: (year, week, destination_tag, trigger_count)."""
    cursor = conn.cursor()
    cursor.execute("SELECT year, week, destination_tag, trigger_count FROM dbo.v_trigger_counts_weekly ORDER BY year, week;")
    return cursor.fetchall()
