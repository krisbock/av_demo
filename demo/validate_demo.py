"""Validate the deterministic local fixture and repository guardrails."""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import fields
from pathlib import Path
from typing import Sequence

from av_demo.config import load_config
from av_demo.generate_demo_data import generate_demo_data
from av_demo.lifecycle import CaseFact, build_case_facts
from av_demo.metrics import calculate_metrics
from av_demo.quality import evaluate_quality

LOGGER = logging.getLogger(__name__)
RESTRICTED_COLUMNS = {"patient_id_hash", "crew_id_hash"}
EXPECTED_METRICS = {
    "active_cases": 40,
    "completed_cases": 160,
    "average_mobilisation_minutes": 5.17,
    "average_hospital_handover_minutes": 36.41,
    "handovers_over_40_minutes": 83,
    "data_quality_exceptions": 2,
}


def validate(project_root: Path, config_path: Path) -> list[str]:
    """Return validation failures for the generated demonstration fixture."""
    failures: list[str] = []
    config = load_config(config_path)
    generated = generate_demo_data(config)
    quality = evaluate_quality(generated.cad_events, generated.hospital_arrivals)
    case_facts = build_case_facts(
        quality.accepted_cad_events,
        quality.accepted_hospital_arrivals,
        config.as_of_timestamp_utc,
    )
    metrics = calculate_metrics(case_facts, len(quality.results))

    if len(case_facts) != config.case_count:
        failures.append(f"Expected {config.case_count} case facts, found {len(case_facts)}")
    expected_exceptions = 2 if config.data_profile == "with_quality_issues" else 0
    if metrics.data_quality_exceptions != expected_exceptions:
        failures.append(
            f"Expected {expected_exceptions} quality exceptions, "
            f"found {metrics.data_quality_exceptions}"
        )
    if config.data_profile == "with_quality_issues" and config.case_count == 200:
        for metric_name, expected_value in EXPECTED_METRICS.items():
            actual_value = getattr(metrics, metric_name)
            if actual_value != expected_value:
                failures.append(
                    f"Metric {metric_name} expected {expected_value}, found {actual_value}"
                )
    if RESTRICTED_COLUMNS.intersection(field.name for field in fields(CaseFact)):
        failures.append("A restricted identifier is present in the approved CaseFact model")
    pipeline_source = (project_root / "pipelines/av_demo_pipeline.py").read_text(
        encoding="utf-8"
    )
    for restricted_column in sorted(RESTRICTED_COLUMNS):
        if restricted_column in pipeline_source:
            failures.append(
                f"Restricted identifier is present in pipeline source: {restricted_column}"
            )

    required_paths = (
        "config/genie_instructions.md",
        "config/metric_definitions.yml",
        "pipelines/av_demo_pipeline.py",
        "resources/demo_pipeline.yml",
        "sql/verified_queries.sql",
        "powerbi/measures.dax",
        "fabric/semantic_model_spec.md",
    )
    for relative_path in required_paths:
        if not (project_root / relative_path).is_file():
            failures.append(f"Required file is missing: {relative_path}")

    verified_sql = (project_root / "sql/verified_queries.sql").read_text(
        encoding="utf-8"
    )
    if verified_sql.count("-- Q") < 3:
        failures.append("Verified questions do not all have reference SQL")

    genie_instructions = (project_root / "config/genie_instructions.md").read_text(
        encoding="utf-8"
    )
    for guardrail in ("reporting window", "patient_id_hash", "crew_id_hash", "refuse"):
        if guardrail.casefold() not in genie_instructions.casefold():
            failures.append(f"Genie instructions are missing guardrail: {guardrail}")

    markdown_files = [
        project_root / "README.md",
        project_root / "ARCHITECTURE.md",
        project_root / "DEMO_SCRIPT.md",
        *sorted((project_root / "config").glob("*.md")),
        *sorted((project_root / "fabric").glob("*.md")),
        *sorted((project_root / "powerbi").glob("*.md")),
    ]
    for markdown_file in markdown_files:
        content = markdown_file.read_text(encoding="utf-8")
        for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            target = raw_target.strip("<>").split("#", maxsplit=1)[0]
            if not target or "://" in target:
                continue
            if not (markdown_file.parent / target).resolve().exists():
                failures.append(
                    f"Broken documentation reference in {markdown_file.name}: {target}"
                )
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    """Run local validation and return a process exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/demo_config.example.yml"),
    )
    arguments = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    project_root = Path(__file__).resolve().parents[1]
    failures = validate(project_root, arguments.config)
    if failures:
        for failure in failures:
            LOGGER.error("FAIL: %s", failure)
        return 1
    LOGGER.info("PASS: deterministic fixture and repository guardrails validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
