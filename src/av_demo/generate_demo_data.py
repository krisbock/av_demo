"""Deterministic synthetic source-data generation."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from av_demo.config import DemoConfig, load_config
from av_demo.models import CadEvent, HospitalArrival

LOGGER = logging.getLogger(__name__)

EVENT_SEQUENCE = (
    "CASE_CREATED",
    "UNIT_DISPATCHED",
    "UNIT_ON_SCENE",
    "ARRIVED_HOSPITAL",
    "HANDOVER_COMPLETED",
    "UNIT_CLEARED",
)
REGIONS = ("CENTRAL", "EAST", "NORTH", "WEST")
HOSPITALS = tuple(f"Synthetic Hospital {letter}" for letter in "ABCDE")
PRIORITIES = ("Priority 1", "Priority 2", "Priority 3")


@dataclass(frozen=True)
class GeneratedData:
    """Generated source rows for one repeatable demonstration."""

    cad_events: tuple[CadEvent, ...]
    hospital_arrivals: tuple[HospitalArrival, ...]


def _event(
    case_number: int,
    event_number: int,
    unit_id: str,
    event_type: str,
    event_time: datetime,
    priority: str,
    region: str,
) -> CadEvent:
    """Build one stable CAD event."""
    return CadEvent(
        event_id=f"EVT-{case_number:06d}-{event_number:02d}",
        case_id=f"CASE-{case_number:06d}",
        unit_id=unit_id,
        event_type=event_type,
        event_timestamp_utc=event_time,
        ingestion_timestamp_utc=event_time + timedelta(minutes=(case_number % 4) + 1),
        case_priority=priority,
        region_code=region,
    )


def generate_demo_data(config: DemoConfig) -> GeneratedData:
    """Generate deterministic synthetic CAD and hospital records."""
    rng = random.Random(config.random_seed)
    base = datetime.fromisoformat(f"{config.demo_date}T00:00:00+00:00")
    cad_events: list[CadEvent] = []
    hospital_arrivals: list[HospitalArrival] = []

    for case_number in range(1, config.case_count + 1):
        case_id = f"CASE-{case_number:06d}"
        unit_id = f"UNIT-{((case_number - 1) % config.unit_count) + 1:03d}"
        region = REGIONS[(case_number - 1) % len(REGIONS)]
        hospital = HOSPITALS[(case_number - 1) % len(HOSPITALS)]
        priority = PRIORITIES[rng.randrange(len(PRIORITIES))]
        created = base + timedelta(minutes=rng.randint(0, 540))
        dispatch = created + timedelta(minutes=rng.randint(2, 8))
        on_scene = dispatch + timedelta(minutes=rng.randint(8, 20))
        arrival = on_scene + timedelta(minutes=rng.randint(20, 50))
        handover_complete = arrival + timedelta(minutes=rng.randint(15, 55))
        cleared = handover_complete + timedelta(minutes=rng.randint(5, 15))
        timestamps = (created, dispatch, on_scene, arrival, handover_complete, cleared)

        for event_number, (event_type, event_time) in enumerate(
            zip(EVENT_SEQUENCE, timestamps, strict=True),
            start=1,
        ):
            if event_type == "UNIT_CLEARED" and case_number % 5 == 0:
                continue
            cad_events.append(
                _event(
                    case_number,
                    event_number,
                    unit_id,
                    event_type,
                    event_time,
                    priority,
                    region,
                )
            )

        hospital_arrivals.append(
            HospitalArrival(
                case_id=case_id,
                unit_id=unit_id,
                synthetic_hospital_name=hospital,
                arrival_timestamp_utc=arrival,
                handover_complete_timestamp_utc=handover_complete,
                region_code=region,
            )
        )

    if config.data_profile == "with_quality_issues":
        cad_events.append(cad_events[0])
        first = hospital_arrivals[0]
        hospital_arrivals[0] = HospitalArrival(
            case_id=first.case_id,
            unit_id=first.unit_id,
            synthetic_hospital_name=first.synthetic_hospital_name,
            arrival_timestamp_utc=first.arrival_timestamp_utc,
            handover_complete_timestamp_utc=first.arrival_timestamp_utc - timedelta(minutes=5),
            region_code=first.region_code,
        )

    return GeneratedData(tuple(cad_events), tuple(hospital_arrivals))


def write_generated_data(data: GeneratedData, output_path: Path) -> None:
    """Write generated source rows using OneLake-friendly JSON and CSV files."""
    cad_path = output_path / "cad_events"
    arrivals_path = output_path / "hospital_arrivals"
    cad_path.mkdir(parents=True, exist_ok=True)
    arrivals_path.mkdir(parents=True, exist_ok=True)

    with (cad_path / "cad_events.jsonl").open("w", encoding="utf-8") as handle:
        for record in data.cad_events:
            handle.write(json.dumps(record.as_record(), sort_keys=True) + "\n")

    fields = list(data.hospital_arrivals[0].as_record())
    with (arrivals_path / "hospital_arrivals.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(record.as_record() for record in data.hospital_arrivals)


def main(argv: Sequence[str] | None = None) -> int:
    """Generate configured demonstration data."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/demo_config.example.yml"),
    )
    arguments = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config = load_config(arguments.config)
    data = generate_demo_data(config)
    write_generated_data(data, config.generated_data_path)
    LOGGER.info(
        "Generated %d CAD events and %d hospital arrivals in %s",
        len(data.cad_events),
        len(data.hospital_arrivals),
        config.generated_data_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
