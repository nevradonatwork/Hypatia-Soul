import os

from flask import Flask, render_template, request, redirect, url_for, session

import db
import logic
from translations import TEXT, t

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")  # only used for the language cookie


def current_lang() -> str:
    return request.args.get("lang") or session.get("lang", "en")


@app.route("/")
def index():
    lang = current_lang()
    session["lang"] = lang
    return render_template("form.html", lang=lang, T=TEXT[lang])


@app.route("/submit", methods=["POST"])
def submit():
    lang = current_lang()
    form = request.form

    payload = {
        "language": lang,
        "source_label": form.get("source_label", "Unreasonable situation"),
        "raw_description": form.get("raw_description", ""),
        "extract_fact": form.get("extract_fact", ""),
        "extract_third_party_version": form.get("extract_third_party_version"),
        "extract_is_evidence_based": form.get("extract_is_evidence_based") == "yes",
        "extract_is_recurring_pattern": form.get("extract_is_recurring_pattern") == "yes",
        "transform_intensity_score": form.get("transform_intensity_score"),
        "transform_is_proportional": form.get("transform_is_proportional") == "yes",
        "transform_signal_type": form.get("transform_signal_type"),
        "transform_serves_purpose": form.get("transform_serves_purpose") == "yes",
        "filter_feels_familiar": form.get("filter_feels_familiar") == "yes",
        "filter_reaction_vs_event_size": form.get("filter_reaction_vs_event_size"),
        "filter_would_react_same_stranger": form.get("filter_would_react_same_stranger") == "yes",
        "filter_echoes_childhood": form.get("filter_echoes_childhood") == "yes",
        "destination_note": form.get("destination_note"),
    }

    # Use the manual override if provided, otherwise auto-suggest
    manual_tag = form.get("destination_tag")
    payload["destination_tag"] = manual_tag if manual_tag in logic.VALID_TAGS else logic.suggest_destination(payload)

    errors = logic.validate_event_payload(payload)
    if errors:
        return render_template("form.html", lang=lang, T=TEXT[lang], errors=errors, values=payload), 400

    conn = db.get_connection()
    try:
        db.insert_event(conn, payload)
    finally:
        conn.close()

    return redirect(url_for("counts", lang=lang))


@app.route("/counts")
def counts():
    lang = current_lang()
    conn = db.get_connection()
    try:
        totals = db.get_total_counts(conn)
        weekly = db.get_weekly_counts(conn)
    finally:
        conn.close()
    return render_template("counts.html", lang=lang, T=TEXT[lang], totals=totals, weekly=weekly)


if __name__ == "__main__":
    app.run(debug=True, port=5050)
