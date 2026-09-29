"""Tests for lifecycle reconstruction and canonical metrics."""

from datetime import datetime
from pathlib import Path

from av_demo.config import DemoConfig
from av_demo.generate_demo_data import generate_demo_data
from av_demo.lifecycle import build_case_facts
from av_demo.metrics import calculate_metrics
from av_demo.quality import evaluate_quality


def test_case_lifecycle_and_metrics() -> None:
    """The fixed fixture has stable case-state and metric values."""
    config = DemoConfig(
        catalog="av_demo",
        raw_catalog="onelake_demo",
        raw_schema="raw_av",
        demo_date="2026-09-15",
        as_of_timestamp_utc=datetime.fromisoformat("2026-09-15T12:00:00+00:00"),
        random_seed=42,
        case_count=200,
        unit_count=10,
        data_profile="with_quality_issues",
        generated_data_path=Path("generated/raw_av"),
        demo_environment=True,
    )
    generated = generate_demo_data(config)
    quality = evaluate_quality(generated.cad_events, generated.hospital_arrivals)
    facts = build_case_facts(
        quality.accepted_cad_events,
        quality.accepted_hospital_arrivals,
        config.as_of_timestamp_utc,
    )
    metrics = calculate_metrics(facts, len(quality.results))
    assert len(facts) == 200
    assert metrics.active_cases == 40
    assert metrics.completed_cases == 160
    assert metrics.average_mobilisation_minutes == 5.17
    assert metrics.average_hospital_handover_minutes == 36.41
    assert metrics.handovers_over_40_minutes == 83
    assert metrics.data_quality_exceptions == 2


def test_future_events_do_not_affect_current_state() -> None:
    """A cutoff before dispatch leaves the case active without a duration."""
    config = DemoConfig(
        catalog="av_demo",
        raw_catalog="onelake_demo",
        raw_schema="raw_av",
        demo_date="2026-09-15",
        as_of_timestamp_utc=datetime.fromisoformat("2026-09-15T00:00:00+00:00"),
        random_seed=1,
        case_count=1,
        unit_count=1,
        data_profile="clean",
        generated_data_path=Path("generated/raw_av"),
        demo_environment=True,
    )
    generated = generate_demo_data(config)
    facts = build_case_facts(
        generated.cad_events,
        generated.hospital_arrivals,
        generated.cad_events[0].event_timestamp_utc,
    )
    assert facts[0].active_flag
    assert facts[0].mobilisation_minutes is None
    assert facts[0].hospital_handover_minutes is None
