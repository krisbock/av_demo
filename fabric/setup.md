# Fabric Setup

This guide covers presentation assets only. It assumes synthetic source data and approved Databricks gold objects already exist.

## Fixed scope

- Demonstration date: 15 September 2026
- Snapshot: `2026-09-15T12:00:00Z`
- Approved objects: `fact_case`, `dim_region`, `dim_hospital`, `operational_metrics`
- Required model mode: Direct Lake

## Pre-staged prerequisites

- A Fabric capacity and workspace approved for Copilot.
- A Fabric OneLake landing area containing the fixed synthetic CAD and hospital snapshot.
- Databricks read-only OneLake catalog federation already validated.
- Unity Catalog silver and gold processing already completed.
- The four approved gold objects available for Fabric mirroring.
- Access groups agreed for Fabric administrators, report authors and report viewers.

No live ingestion, transformation or permission changes are part of the presentation.

## Portal-only/manual setup

The following activities are performed in product portals. Portal labels can vary by release; use the supported user interface for the tenant rather than scripting undocumented operations.

### 1. Fabric workspace

1. In the Fabric portal, create or select the dedicated demonstration workspace.
2. Assign it to the approved Fabric capacity.
3. Grant workspace roles to the approved demonstration groups only.
4. Confirm Copilot is permitted by tenant and capacity settings.

### 2. OneLake landing

1. In Fabric, open the pre-staged Lakehouse.
2. Upload `generated/raw_av/cad_events/cad_events.jsonl` beneath
   `Files/raw_av/cad_events/`.
3. Upload `generated/raw_av/hospital_arrivals/hospital_arrivals.csv` beneath
   `Files/raw_av/hospital_arrivals/`.
4. Create a Fabric notebook from `load_raw_tables.py`, attach the Lakehouse and
   run it to materialise `raw_av.cad_events` and `raw_av.hospital_arrivals` as
   Delta tables.
5. Confirm both synthetic tables contain the fixed snapshot.
6. Confirm the source metadata displays `2026-09-15T12:00:00Z`.
7. Verify the Databricks identity has read-only access; it must not have write permission.

### 3. Mirror approved Unity Catalog gold objects

1. In the Fabric portal, create or open the supported mirrored database item for the Databricks source.
2. Select only:
   - `fact_case`
   - `dim_region`
   - `dim_hospital`
   - `operational_metrics`
3. Confirm `patient_id_hash` and `crew_id_hash` do not exist in the selected source schemas. Do not rely on hiding columns after mirroring.
4. Start or resume mirroring using the portal.
5. Wait for the portal to report a successful initial sync.
6. Inspect row counts and snapshot timestamps against the approved gold validation record.

### 4. Create the Direct Lake semantic model

1. In Fabric, create a semantic model from the mirrored objects.
2. Select Direct Lake storage mode.
3. Add the four approved objects only.
4. Apply table, column, relationship and measure definitions from `semantic_model_spec.md`.
5. Add the measures from `../powerbi/measures.dax`.
6. Mark the six measures as certified or otherwise endorsed using the organisation's governance process.
7. Apply the model descriptions and synonyms before enabling self-service use.
8. Confirm the model does not contain `patient_id_hash` or `crew_id_hash`.

### 5. Configure Power BI and Copilot

1. Build the prepared overview report against the Direct Lake semantic model.
2. Add an obvious banner: **Synthetic data — 15 September 2026 — As at 12:00 UTC**.
3. Add cards for all six certified measures.
4. Add region and hospital breakdown visuals.
5. Apply `../powerbi/copilot_instructions.md` in the supported model or Copilot instruction experience.
6. Test the approved prompts in `../DEMO_SCRIPT.md`.
7. Save a successful report view and AI response for recovery.

## Validation checklist

- [ ] Landing contains synthetic CAD and hospital data only.
- [ ] Snapshot is `2026-09-15T12:00:00Z`.
- [ ] Databricks access to OneLake landing is read-only.
- [ ] Mirror contains exactly the four approved objects.
- [ ] Mirror initial sync is successful and row counts agree with gold validation.
- [ ] `patient_id_hash` is physically absent.
- [ ] `crew_id_hash` is physically absent.
- [ ] Semantic model reports Direct Lake mode.
- [ ] Relationships are active and filters flow from dimensions to facts.
- [ ] All six measures return expected approved totals.
- [ ] Copilot answers use certified measures and fixed-snapshot language.
- [ ] Workspace and item permissions are limited to approved groups.

## Recovery

| Failure | Safe recovery |
|---|---|
| Mirror is stale | Show the last successful sync time. Use the prepared fixed-snapshot report; do not restart or rebuild during the presentation. |
| Direct Lake query fails | Use the pre-captured report page and certified measure export. Disclose the capture time. |
| Copilot is unavailable | Present the prepared narrative and report visuals. |
| Access is denied | Use the presenter account validated during preflight; do not broaden permissions live. |
| A prohibited column appears | Stop using the affected model or mirror. Remove it from the source gold contract, recreate/synchronise the asset through the portal, and repeat validation before any demonstration. |
| Values differ between tools | Stop the AI comparison, apply the fixed date and as-of filters, and reconcile against the approved gold validation record before continuing. |
