"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from av_demo.errors import NotFoundError, ValidationError


@dataclass(frozen=True)
class DemoConfig:
    """Validated configuration for deterministic data generation."""

    catalog: str
    raw_catalog: str
    raw_schema: str
    demo_date: str
    as_of_timestamp_utc: datetime
    random_seed: int
    case_count: int
    unit_count: int
    data_profile: str
    generated_data_path: Path
    demo_environment: bool


def _required(mapping: dict[str, Any], key: str) -> Any:
    """Return a required configuration value."""
    if key not in mapping:
        raise ValidationError(f"Missing required configuration value: {key}")
    return mapping[key]


def load_config(path: Path) -> DemoConfig:
    """Load and validate a YAML demonstration configuration."""
    if not path.exists():
        raise NotFoundError(f"Configuration file does not exist: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValidationError("Configuration root must be a mapping")

    profile = str(_required(raw, "data_profile"))
    if profile not in {"clean", "with_quality_issues"}:
        raise ValidationError("data_profile must be clean or with_quality_issues")

    case_count = int(_required(raw, "case_count"))
    unit_count = int(_required(raw, "unit_count"))
    if case_count < 1 or unit_count < 1:
        raise ValidationError("case_count and unit_count must be positive")

    as_of = datetime.fromisoformat(str(_required(raw, "as_of_timestamp_utc")))
    if as_of.tzinfo is None:
        raise ValidationError("as_of_timestamp_utc must include a UTC offset")

    demo_environment = _required(raw, "demo_environment")
    if not isinstance(demo_environment, bool):
        raise ValidationError("demo_environment must be a YAML Boolean")

    return DemoConfig(
        catalog=str(_required(raw, "catalog")),
        raw_catalog=str(_required(raw, "raw_catalog")),
        raw_schema=str(_required(raw, "raw_schema")),
        demo_date=str(_required(raw, "demo_date")),
        as_of_timestamp_utc=as_of,
        random_seed=int(_required(raw, "random_seed")),
        case_count=case_count,
        unit_count=unit_count,
        data_profile=profile,
        generated_data_path=Path(str(_required(raw, "generated_data_path"))),
        demo_environment=demo_environment,
    )
