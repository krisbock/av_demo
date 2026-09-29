# Direct Lake Semantic Model Specification

## Model contract

**Model name:** AV Operational Snapshot  
**Storage mode:** Direct Lake  
**Demonstration date:** 15 September 2026  
**As at:** `2026-09-15T12:00:00Z`

The model contains only approved mirrored gold objects. `patient_id_hash` and `crew_id_hash` must be physically excluded upstream and must not be present in the mirror or semantic model.

## Objects

### `fact_case`

Grain: one synthetic ambulance case current at the snapshot.

| Column | Type | Model treatment |
|---|---|---|
| `case_id` | text | Hidden key; synthetic identifier |
| `region_code` | text | Hidden relationship key |
| `case_priority` | text | Visible; synthetic operational priority |
| `synthetic_hospital_name` | text, nullable | Hidden relationship key |
| `created_timestamp_utc` | datetime | Visible; event occurrence time |
| `dispatch_timestamp_utc` | datetime, nullable | Hidden |
| `clear_timestamp_utc` | datetime, nullable | Hidden |
| `mobilisation_minutes` | decimal number, nullable | Visible; summarise by average |
| `hospital_handover_minutes` | decimal number, nullable | Visible; summarise by average |
| `active_flag` | Boolean | Hidden; used by the Active Cases measure |
| `lifecycle_complete_flag` | Boolean | Hidden; used by the Completed Cases measure |

### `dim_region`

Grain: one operational region.

| Column | Type | Model treatment |
|---|---|---|
| `region_code` | text | Visible primary key; friendly name **Region**; sort alphabetically |

### `dim_hospital`

Grain: one synthetic receiving hospital.

| Column | Type | Model treatment |
|---|---|---|
| `synthetic_hospital_name` | text | Visible primary key; friendly name **Synthetic Hospital**; sort alphabetically |

### `operational_metrics`

Grain: one approved snapshot row for the fixed reporting date, used for reconciliation.

| Column | Type | Model treatment |
|---|---|---|
| `reporting_date` | date | Visible |
| `active_cases` | whole number | Hidden reconciliation value |
| `completed_cases` | whole number | Hidden reconciliation value |
| `average_mobilisation_minutes` | decimal number | Hidden reconciliation value |
| `average_hospital_handover_minutes` | decimal number | Hidden reconciliation value |
| `handovers_over_40_minutes` | whole number | Hidden reconciliation value |
| `data_quality_exceptions` | whole number | Hidden; source for the certified exception measure |

Five certified case and duration measures are calculated from `fact_case`.
`Data Quality Exceptions` uses the approved snapshot value in
`operational_metrics`; the remaining reconciliation columns are not substitute
measure sources during the demonstration.

## Relationships

| From | To | Cardinality | Filter direction | Active |
|---|---|---|---|---|
| `dim_region[region_code]` | `fact_case[region_code]` | one-to-many | Single | Yes |
| `dim_hospital[synthetic_hospital_name]` | `fact_case[synthetic_hospital_name]` | one-to-many | Single | Yes |

Keep `operational_metrics` disconnected because it is a whole-snapshot reconciliation table.

## Measures

Create these measures exactly as defined in `../powerbi/measures.dax`:

1. Active Cases
2. Completed Cases
3. Average Mobilisation Minutes
4. Average Hospital Handover Minutes
5. Handovers Over 40 Minutes
6. Data Quality Exceptions

Formatting:

- Case and exception measures: whole number with thousands separator.
- Average duration measures: decimal number with one decimal place.
- Display folder: `Operational measures`.
- Description prefix: `Certified measure for the synthetic fixed snapshot.`

## Business descriptions and synonyms

| Model item | Description | Suggested synonyms |
|---|---|---|
| `fact_case` | Synthetic operational ambulance cases at the fixed snapshot. | cases, incidents, ambulance cases |
| `dim_region[region_code]` | Synthetic operational region. | region, area |
| `dim_hospital[synthetic_hospital_name]` | Synthetic receiving hospital used for demonstration. | hospital, destination |
| `mobilisation_minutes` | Minutes from case creation to unit dispatch. | mobilisation time, mobilization time |
| `hospital_handover_minutes` | Minutes from hospital arrival to completed handover. | handover time, transfer time |
| Active Cases | Count of cases with status Active. | open cases, current cases |
| Completed Cases | Count of cases with status Completed. | closed cases, finished cases |
| Data Quality Exceptions | Count of cases flagged for data quality review. | quality issues, data exceptions |

## Default presentation filters

- `operational_metrics[reporting_date]` = 15 September 2026
- The report subtitle states `As at 2026-09-15T12:00:00Z`.

Display the date and snapshot in report titles. The model represents a fixed operational snapshot, not a real-time feed.

## Security and AI readiness

- Grant Build permission only to approved report authors and AI users.
- Use workspace and item permissions approved for the demonstration.
- Do not add patient, crew, free-text notes, addresses or clinical fields.
- Copilot and Genie must use approved object and measure names.
- AI-generated narratives must not infer causation, patient outcomes, clinical priorities or individual staff performance.
- Validate AI totals against the six certified measures before presenting.

## Acceptance checks

1. Storage mode is Direct Lake.
2. Exactly four approved objects are present.
3. Both prohibited hash columns are absent from source schemas, mirror metadata and model metadata.
4. `region_code` and `synthetic_hospital_name` are unique in their dimensions.
5. There are no orphan non-null region or hospital values in `fact_case`.
6. Durations are null or non-negative.
7. The six measures agree with the approved gold validation record under default filters.
8. Copilot recognises Australian spelling and fixed-snapshot context.
