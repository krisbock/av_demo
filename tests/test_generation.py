"""Tests for deterministic synthetic source generation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from av_demo.config import DemoConfig, load_config
from av_demo.errors import NotFoundError, ValidationError
from av_demo.generate_demo_data import generate_demo_data, main, write_generated_data


@pytest.fixture
def config() -> DemoConfig:
    """Return a compact deterministic test configuration."""
    return DemoConfig(
        catalog="av_demo",
        raw_catalog="onelake_demo",
        raw_schema="raw_av",
        demo_date="2026-09-15",
        as_of_timestamp_utc=__import__("datetime").datetime.fromisoformat(
            "2026-09-15T12:00:00+00:00"
        ),
        random_seed=42,
        case_count=10,
        unit_count=3,
        data_profile="with_quality_issues",
        generated_data_path=Path("generated/raw_av"),
        demo_environment=True,
    )


def test_generation_is_deterministic(config: DemoConfig) -> None:
    """A fixed seed and demonstration clock produce identical rows."""
    first = generate_demo_data(config)
    second = generate_demo_data(config)
    assert first == second
    assert len(first.cad_events) == 59
    assert len(first.hospital_arrivals) == 10
    assert first.cad_events[-1] == first.cad_events[0]


def test_clean_profile_has_no_injected_duplicate(config: DemoConfig) -> None:
    """The clean fixture contains no controlled quality exceptions."""
    data = generate_demo_data(replace(config, data_profile="clean"))
    assert len(data.cad_events) == 58
    assert data.hospital_arrivals[0].handover_complete_timestamp_utc > (
        data.hospital_arrivals[0].arrival_timestamp_utc
    )


def test_write_generated_data(config: DemoConfig, tmp_path: Path) -> None:
    """Generated rows are written using the documented source formats."""
    data = generate_demo_data(config)
    write_generated_data(data, tmp_path)
    cad_lines = (tmp_path / "cad_events/cad_events.jsonl").read_text().splitlines()
    arrivals = (tmp_path / "hospital_arrivals/hospital_arrivals.csv").read_text()
    assert json.loads(cad_lines[0])["case_id"] == "CASE-000001"
    assert "synthetic_hospital_name" in arrivals


def test_load_config_and_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The example configuration loads and the command writes its fixture."""
    config_path = tmp_path / "config.yml"
    output_path = tmp_path / "generated/raw_av"
    config_path.write_text(
        "\n".join(
            (
                "catalog: av_demo",
                "raw_catalog: onelake_demo",
                "raw_schema: raw_av",
                'demo_date: "2026-09-15"',
                'as_of_timestamp_utc: "2026-09-15T12:00:00+00:00"',
                "random_seed: 42",
                "case_count: 2",
                "unit_count: 1",
                "data_profile: clean",
                f"generated_data_path: {output_path}",
                "demo_environment: true",
            )
        ),
        encoding="utf-8",
    )
    loaded = load_config(config_path)
    assert loaded.case_count == 2
    assert main(["--config", str(config_path)]) == 0
    assert (output_path / "cad_events/cad_events.jsonl").is_file()


def test_invalid_configurations_raise(tmp_path: Path) -> None:
    """Missing and malformed configuration values fail explicitly."""
    with pytest.raises(NotFoundError):
        load_config(tmp_path / "missing.yml")
    invalid = tmp_path / "invalid.yml"
    invalid.write_text("[]", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(invalid)
    invalid.write_text("data_profile: other", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(invalid)


def test_demo_environment_requires_yaml_boolean(tmp_path: Path) -> None:
    """Quoted Boolean-like values cannot weaken reset safety."""
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "\n".join(
            (
                "catalog: av_demo",
                "raw_catalog: onelake_demo",
                "raw_schema: raw_av",
                'demo_date: "2026-09-15"',
                'as_of_timestamp_utc: "2026-09-15T12:00:00+00:00"',
                "random_seed: 42",
                "case_count: 1",
                "unit_count: 1",
                "data_profile: clean",
                "generated_data_path: generated/raw_av",
                'demo_environment: "false"',
            )
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="YAML Boolean"):
        load_config(config_path)
