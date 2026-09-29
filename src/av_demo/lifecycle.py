"""Case-lifecycle reconstruction without future-event leakage."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from av_demo.models import CadEvent, HospitalArrival


@dataclass(frozen=True)
class CaseFact:
    """One curated synthetic case at a configured point in time."""

    case_id: str
    region_code: str
    case_priority: str
    synthetic_hospital_name: str | None
    created_timestamp_utc: datetime
    dispatch_timestamp_utc: datetime | None
    clear_timestamp_utc: datetime | None
    mobilisation_minutes: float | None
    hospital_handover_minutes: float | None
    active_flag: bool
    lifecycle_complete_flag: bool


def _minutes(start: datetime | None, end: datetime | None) -> float | None:
    """Return elapsed minutes when both timestamps are available."""
    if start is None or end is None:
        return None
    return (end - start).total_seconds() / 60


def build_case_facts(
    cad_events: Iterable[CadEvent],
    hospital_arrivals: Iterable[HospitalArrival],
    as_of_timestamp_utc: datetime,
) -> tuple[CaseFact, ...]:
    """Build case facts using only information known by the as-of timestamp."""
    events_by_case: dict[str, list[CadEvent]] = defaultdict(list)
    for event in cad_events:
        if event.event_timestamp_utc <= as_of_timestamp_utc:
            events_by_case[event.case_id].append(event)

    arrivals_by_case = {
        arrival.case_id: arrival
        for arrival in hospital_arrivals
        if arrival.arrival_timestamp_utc <= as_of_timestamp_utc
        and arrival.handover_complete_timestamp_utc <= as_of_timestamp_utc
    }
    facts: list[CaseFact] = []

    for case_id, events in sorted(events_by_case.items()):
        ordered_events = sorted(
            events,
            key=lambda event: (event.event_timestamp_utc, event.event_id),
        )
        timestamps: dict[str, datetime] = {}
        for event in ordered_events:
            timestamps.setdefault(event.event_type, event.event_timestamp_utc)

        created = timestamps.get("CASE_CREATED")
        if created is None:
            continue
        dispatch = timestamps.get("UNIT_DISPATCHED")
        cleared = timestamps.get("UNIT_CLEARED")
        arrival = arrivals_by_case.get(case_id)
        facts.append(
            CaseFact(
                case_id=case_id,
                region_code=ordered_events[0].region_code,
                case_priority=ordered_events[0].case_priority,
                synthetic_hospital_name=(
                    arrival.synthetic_hospital_name if arrival else None
                ),
                created_timestamp_utc=created,
                dispatch_timestamp_utc=dispatch,
                clear_timestamp_utc=cleared,
                mobilisation_minutes=_minutes(created, dispatch),
                hospital_handover_minutes=(
                    _minutes(
                        arrival.arrival_timestamp_utc,
                        arrival.handover_complete_timestamp_utc,
                    )
                    if arrival
                    else None
                ),
                active_flag=cleared is None,
                lifecycle_complete_flag=cleared is not None,
            )
        )

    return tuple(facts)

