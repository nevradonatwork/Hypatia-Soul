"""Business logic: decide whether an event goes to 'system' or 'archive'."""

VALID_TAGS = ("system", "archive")


def suggest_destination(answers: dict) -> str:
    """Suggest a destination tag based on the transform/filter answers.

    Rule of thumb:
    - If the transform stage says the feeling means 'action is needed',
      it goes to 'system' (lawyer, court, record).
    - Otherwise (needs processing, or unclear) it goes to 'archive'
      (old emotion, quarantined, not acted on immediately).

    This is a suggestion only, not a survey. The user can always
    override it before saving.
    """
    signal = answers.get("transform_signal_type")
    if signal == "action_needed":
        return "system"
    return "archive"


def validate_event_payload(payload: dict) -> list:
    """Return a list of validation error messages. Empty list = valid."""
    errors = []

    if not payload.get("raw_description", "").strip():
        errors.append("raw_description is required")

    if not payload.get("extract_fact", "").strip():
        errors.append("extract_fact is required")

    intensity = payload.get("transform_intensity_score")
    if intensity is not None:
        try:
            intensity = int(intensity)
            if not (1 <= intensity <= 10):
                errors.append("transform_intensity_score must be between 1 and 10")
        except (TypeError, ValueError):
            errors.append("transform_intensity_score must be a number")

    tag = payload.get("destination_tag")
    if tag is not None and tag not in VALID_TAGS:
        errors.append(f"destination_tag must be one of {VALID_TAGS}")

    lang = payload.get("language", "en")
    if lang not in ("en", "tr"):
        errors.append("language must be 'en' or 'tr'")

    return errors
