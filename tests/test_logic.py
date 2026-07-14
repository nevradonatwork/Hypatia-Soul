import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logic


def test_suggest_destination_action_needed_goes_to_system():
    answers = {"transform_signal_type": "action_needed"}
    assert logic.suggest_destination(answers) == "system"


def test_suggest_destination_needs_processing_goes_to_archive():
    answers = {"transform_signal_type": "needs_processing"}
    assert logic.suggest_destination(answers) == "archive"


def test_suggest_destination_missing_signal_defaults_to_archive():
    assert logic.suggest_destination({}) == "archive"


def test_validate_event_payload_requires_raw_description():
    payload = {"raw_description": "", "extract_fact": "he did X"}
    errors = logic.validate_event_payload(payload)
    assert "raw_description is required" in errors


def test_validate_event_payload_requires_extract_fact():
    payload = {"raw_description": "something happened", "extract_fact": "  "}
    errors = logic.validate_event_payload(payload)
    assert "extract_fact is required" in errors


def test_validate_event_payload_intensity_out_of_range():
    payload = {
        "raw_description": "x", "extract_fact": "y",
        "transform_intensity_score": "15",
    }
    errors = logic.validate_event_payload(payload)
    assert any("transform_intensity_score" in e for e in errors)


def test_validate_event_payload_intensity_not_a_number():
    payload = {
        "raw_description": "x", "extract_fact": "y",
        "transform_intensity_score": "high",
    }
    errors = logic.validate_event_payload(payload)
    assert any("transform_intensity_score" in e for e in errors)


def test_validate_event_payload_valid_tag():
    payload = {"raw_description": "x", "extract_fact": "y", "destination_tag": "not_a_tag"}
    errors = logic.validate_event_payload(payload)
    assert any("destination_tag" in e for e in errors)


def test_validate_event_payload_valid_language():
    payload = {"raw_description": "x", "extract_fact": "y", "language": "fr"}
    errors = logic.validate_event_payload(payload)
    assert any("language" in e for e in errors)


def test_validate_event_payload_happy_path_no_errors():
    payload = {
        "raw_description": "he did not hand over the documents",
        "extract_fact": "documents withheld on the agreed date",
        "transform_intensity_score": "7",
        "destination_tag": "system",
        "language": "en",
    }
    assert logic.validate_event_payload(payload) == []
