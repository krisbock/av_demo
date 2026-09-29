"""Deterministic data-quality checks shared by local tests and notebooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Iterable

from av_demo.errors import ValidationError
from av_demo.models import CadEvent, HospitalArrival, QualityResult

SUPPORTED_RULE_IDS = frozenset({"DQ-001", "DQ-002"})


@dataclass(frozen=True)
class QualityEvaluation:
    """Accepted records and failed quality-rule results."""

    accepted_cad_events: tuple[CadEvent, ...]
    accepted_hospital_arrivals: tuple[HospitalArrival, ...]
    results: tuple[QualityResult, ...]


def evaluate_quality(
    cad_events: Iterable[CadEvent],
    hospital_arrivals: Iterable[HospitalArrival],
    enabled_rule_ids: Collection[str] = SUPPORTED_RULE_IDS,
) -> QualityEvaluation:
    """Evaluate configured rules and return valid source records."""
    unknown_rules = set(enabled_rule_ids) - SUPPORTED_RULE_IDS
    if unknown_rules:
        raise ValidationError(f"Unsupported data-quality rules: {sorted(unknown_rules)}")

    accepted_events: list[CadEvent] = []
    accepted_arrivals: list[HospitalArrival] = []
    results: list[QualityResult] = []
    seen_event_ids: set[str] = set()

    for event in cad_events:
        if "DQ-001" in enabled_rule_ids and event.event_id in seen_event_ids:
            results.append(
                QualityResult(
                    rule_id="DQ-001",
                    rule_name="Unique CAD event identifier",
                    dataset_name="cad_events",
                    record_identifier=event.event_id,
                    severity="HIGH",
                    observed_value=event.event_id,
                    expected_condition="event_id must be unique",
                )
            )
            continue
        seen_event_ids.add(event.event_id)
        accepted_events.append(event)

    for arrival in hospital_arrivals:
        if (
            "DQ-002" in enabled_rule_ids
            and arrival.handover_complete_timestamp_utc
            < arrival.arrival_timestamp_utc
        ):
            results.append(
                QualityResult(
                    rule_id="DQ-002",
                    rule_name="Handover completion follows arrival",
                    dataset_name="hospital_arrivals",
                    record_identifier=arrival.case_id,
                    severity="CRITICAL",
                    observed_value=arrival.handover_complete_timestamp_utc.isoformat(),
                    expected_condition=(
                        "handover_complete_timestamp_utc >= arrival_timestamp_utc"
                    ),
                )
            )
            continue
        accepted_arrivals.append(arrival)

    return QualityEvaluation(
        accepted_cad_events=tuple(accepted_events),
        accepted_hospital_arrivals=tuple(accepted_arrivals),
        results=tuple(results),
    )

