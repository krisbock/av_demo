"""Tests for controlled data-quality scenarios."""

from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

from av_demo.config import DemoConfig
from av_demo.errors import ValidationError
from av_demo.generate_demo_data import generate_demo_data
from av_demo.quality import evaluate_quality


def _config(profile: str = "with_quality_issues") -> DemoConfig:
    return DemoConfig(
        catalog="av_demo",
        raw_catalog="onelake_demo",
        raw_schema="raw_av",
        demo_date="2026-09-15",
        as_of_timestamp_utc=datetime.fromisoformat("2026-09-15T12:00:00+00:00"),
        random_seed=42,
        case_count=20,
        unit_count=5,
        data_profile=profile,
        generated_data_path=Path("generated/raw_av"),
        demo_environment=True,
    )


def test_controlled_quality_profile_has_two_exceptions() -> None:
    """The presentation profile always generates its two explained failures."""
    data = generate_demo_data(_config())
    evaluation = evaluate_quality(data.cad_events, data.hospital_arrivals)
    assert [result.rule_id for result in evaluation.results] == ["DQ-001", "DQ-002"]
    assert len(evaluation.accepted_hospital_arrivals) == 19
    assert len({event.event_id for event in evaluation.accepted_cad_events}) == len(
        evaluation.accepted_cad_events
    )


def test_clean_profile_passes() -> None:
    """The clean profile produces no quality failures."""
    data = generate_demo_data(_config("clean"))
    assert evaluate_quality(data.cad_events, data.hospital_arrivals).results == ()


def test_rules_can_be_individually_enabled() -> None:
    """Rule selection is driven by the declarative rule identifiers."""
    data = generate_demo_data(_config())
    result = evaluate_quality(data.cad_events, data.hospital_arrivals, {"DQ-002"})
    assert [failure.rule_id for failure in result.results] == ["DQ-002"]
    assert len(result.accepted_cad_events) == len(data.cad_events)


def test_unknown_rule_is_rejected() -> None:
    """Unknown configured rules cannot silently pass."""
    data = generate_demo_data(_config())
    with pytest.raises(ValidationError):
        evaluate_quality(data.cad_events, data.hospital_arrivals, {"DQ-999"})

