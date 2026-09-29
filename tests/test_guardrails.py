"""Tests for repository validation and reset guardrails."""

from pathlib import Path

import pytest

from av_demo.errors import ConflictError
from demo.reset_demo import reset_generated_data
from demo.validate_demo import validate

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_repository_validation_passes() -> None:
    """The checked-in fixture configuration and documentation are consistent."""
    assert validate(
        PROJECT_ROOT,
        PROJECT_ROOT / "config/demo_config.example.yml",
    ) == []


def test_reset_removes_only_nested_generated_path(tmp_path: Path) -> None:
    """Reset deletes the configured nested fixture and preserves its parent."""
    generated = tmp_path / "generated/raw_av"
    generated.mkdir(parents=True)
    (generated / "fixture.json").write_text("{}", encoding="utf-8")
    config = tmp_path / "config.yml"
    config.write_text(
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
                "demo_environment: true",
            )
        ),
        encoding="utf-8",
    )
    removed = reset_generated_data(tmp_path, config)
    assert removed == generated
    assert not generated.exists()
    assert (tmp_path / "generated").exists()


def test_reset_rejects_non_demo_environment(tmp_path: Path) -> None:
    """Reset cannot run when the environment is not explicitly a demo."""
    config = tmp_path / "config.yml"
    config.write_text(
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
                "demo_environment: false",
            )
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConflictError):
        reset_generated_data(tmp_path, config)

