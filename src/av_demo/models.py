"""Typed records used by the deterministic demonstration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CadEvent:
    """One synthetic computer-aided dispatch event."""

    event_id: str
    case_id: str
    unit_id: str | None
    event_type: str
    event_timestamp_utc: datetime
    ingestion_timestamp_utc: datetime
    case_priority: str
    region_code: str

    def as_record(self) -> dict[str, Any]:
        """Return a serialisable representation."""
        record = asdict(self)
        record["event_timestamp_utc"] = self.event_timestamp_utc.isoformat()
        record["ingestion_timestamp_utc"] = self.ingestion_timestamp_utc.isoformat()
        return record


@dataclass(frozen=True)
class HospitalArrival:
    """One synthetic hospital handover record."""

    case_id: str
    unit_id: str
    synthetic_hospital_name: str
    arrival_timestamp_utc: datetime
    handover_complete_timestamp_utc: datetime
    region_code: str

    def as_record(self) -> dict[str, str]:
        """Return a serialisable representation."""
        return {
            "case_id": self.case_id,
            "unit_id": self.unit_id,
            "synthetic_hospital_name": self.synthetic_hospital_name,
            "arrival_timestamp_utc": self.arrival_timestamp_utc.isoformat(),
            "handover_complete_timestamp_utc": self.handover_complete_timestamp_utc.isoformat(),
            "region_code": self.region_code,
        }


@dataclass(frozen=True)
class QualityResult:
    """A failed declarative data-quality evaluation."""

    rule_id: str
    rule_name: str
    dataset_name: str
    record_identifier: str
    severity: str
    observed_value: str
    expected_condition: str
