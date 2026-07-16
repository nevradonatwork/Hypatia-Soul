import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session

import db
import logic
from translations import TEXT, t

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")  # session cookie signing key


def current_lang() -> str:
    return request.args.get("lang") or session.get("lang", "en")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", lang=current_lang()))
        return view(*args, **kwargs)
    return wrapped


def yes_no_none(value):
    """Map a yes/no/unsure radio value to True/False/None.

    Anything other than an explicit "yes" or "no" (unanswered, or the
    "unsure" option) is stored as NULL rather than forced into False.
    """
    if value == "yes":
        return True
    if value == "no":
        return False
    return None


@app.route("/register", methods=["GET", "POST"])
def register():
    lang = current_lang()
    session["lang"] = lang

    if request.method == "GET":
        return render_template("register.html", lang=lang, T=TEXT[lang])

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    errors = []
    if not email:
        errors.append(TEXT[lang]["email_required"])
    if len(password) < 8:
        errors.append(TEXT[lang]["password_too_short"])

    conn = db.get_connection()
    try:
        if not errors and db.get_user_by_email(conn, email):
            errors.append(TEXT[lang]["email_taken"])
        if errors:
            return render_template("register.html", lang=lang, T=TEXT[lang], errors=errors), 400
        user_id = db.create_user(conn, email, password)
    finally:
        conn.close()

    session["user_id"] = user_id
    session["email"] = email
    return redirect(url_for("index", lang=lang))


@app.route("/login", methods=["GET", "POST"])
def login():
    lang = current_lang()
    session["lang"] = lang

    if request.method == "GET":
        return render_template("login.html", lang=lang, T=TEXT[lang])

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    conn = db.get_connection()
    try:
        user = db.get_user_by_email(conn, email)
    finally:
        conn.close()

    if user is None or not db.verify_password(user[2], password):
        errors = [TEXT[lang]["invalid_credentials"]]
        return render_template("login.html", lang=lang, T=TEXT[lang], errors=errors), 401

    session["user_id"] = user[0]
    session["email"] = user[1]
    return redirect(url_for("index", lang=lang))


@app.route("/logout")
def logout():
    lang = current_lang()
    session.clear()
    return redirect(url_for("login", lang=lang))


@app.route("/")
@login_required
def index():
    lang = current_lang()
    session["lang"] = lang
    return render_template("form.html", lang=lang, T=TEXT[lang])


@app.route("/submit", methods=["POST"])
@login_required
def submit():
    lang = current_lang()
    form = request.form

    payload = {
        "user_id": session["user_id"],
        "language": lang,
        "source_label": form.get("source_label", "Unreasonable situation"),
        "raw_description": form.get("raw_description", ""),
        "extract_fact": form.get("extract_fact", ""),
        "extract_third_party_version": form.get("extract_third_party_version"),
        "extract_is_evidence_based": yes_no_none(form.get("extract_is_evidence_based")),
        "extract_is_recurring_pattern": yes_no_none(form.get("extract_is_recurring_pattern")),
        "transform_intensity_score": form.get("transform_intensity_score"),
        "transform_is_proportional": yes_no_none(form.get("transform_is_proportional")),
        "transform_signal_type": form.get("transform_signal_type"),
        "transform_serves_purpose": yes_no_none(form.get("transform_serves_purpose")),
        "filter_feels_familiar": yes_no_none(form.get("filter_feels_familiar")),
        "filter_reaction_vs_event_size": form.get("filter_reaction_vs_event_size"),
        "filter_would_react_same_stranger": yes_no_none(form.get("filter_would_react_same_stranger")),
        "filter_echoes_childhood": yes_no_none(form.get("filter_echoes_childhood")),
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
@login_required
def counts():
    lang = current_lang()
    user_id = session["user_id"]
    conn = db.get_connection()
    try:
        totals = db.get_total_counts(conn, user_id)
        weekly = db.get_weekly_counts(conn, user_id)
    finally:
        conn.close()
    return render_template("counts.html", lang=lang, T=TEXT[lang], totals=totals, weekly=weekly)


if __name__ == "__main__":
    app.run(debug=True, port=5050)
