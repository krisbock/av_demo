"""Governed metric calculations for the demonstration fixture."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Iterable

from av_demo.lifecycle import CaseFact


@dataclass(frozen=True)
class OperationalMetrics:
    """Small governed metric set shared by Genie and Power BI."""

    active_cases: int
    completed_cases: int
    average_mobilisation_minutes: float | None
    average_hospital_handover_minutes: float | None
    handovers_over_40_minutes: int
    data_quality_exceptions: int


def _average(values: list[float]) -> float | None:
    """Return a stable two-decimal average for available values."""
    return round(fmean(values), 2) if values else None


def calculate_metrics(
    case_facts: Iterable[CaseFact],
    data_quality_exception_count: int,
) -> OperationalMetrics:
    """Calculate the canonical demonstration metrics."""
    facts = tuple(case_facts)
    mobilisation = [
        fact.mobilisation_minutes
        for fact in facts
        if fact.mobilisation_minutes is not None
    ]
    handovers = [
        fact.hospital_handover_minutes
        for fact in facts
        if fact.hospital_handover_minutes is not None
    ]
    return OperationalMetrics(
        active_cases=sum(fact.active_flag for fact in facts),
        completed_cases=sum(fact.lifecycle_complete_flag for fact in facts),
        average_mobilisation_minutes=_average(mobilisation),
        average_hospital_handover_minutes=_average(handovers),
        handovers_over_40_minutes=sum(value > 40 for value in handovers),
        data_quality_exceptions=data_quality_exception_count,
    )
