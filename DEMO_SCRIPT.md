# Demonstration Script

## Demonstration frame

- **Date shown throughout:** 15 September 2026
- **Data as at:** `2026-09-15T12:00:00Z`
- **Dataset:** synthetic CAD and hospital operational data
- **Message:** one governed gold contract supports both Power BI Copilot and Databricks Genie
- **Suggested duration:** 12–15 minutes

## Preflight — complete before the audience joins

### Pre-staged

- Confirm silver and gold processing completed for the fixed snapshot.
- Confirm the Fabric mirror reports a successful sync after the gold processing time.
- Open the prepared Power BI report on the overview page.
- Open the semantic model and confirm Direct Lake mode.
- Open the prepared Databricks Genie space.
- Save screenshots or exported results for the six headline measures and two AI answers.

### Portal-only/manual checks

- In the Fabric portal, confirm the signed-in presenter can open the mirrored database, semantic model and report.
- In Power BI, confirm Copilot is available for the workspace and tenant.
- In Databricks, confirm the presenter can open Genie but cannot edit the approved gold objects.
- Check that `patient_id_hash` and `crew_id_hash` are absent from the mirror and semantic model field list.
- Set all report filters to 15 September 2026 and confirm the page displays **As at 12:00 UTC**.
- Run one prepared Copilot prompt and one prepared Genie question; compare returned totals with report cards.

If any check fails, use the recovery path for that area rather than changing configuration during the presentation.

## Opening

Say:

> This is a synthetic operational snapshot for 15 September 2026, as at midday UTC. It is not live clinical data. We will follow the same approved metrics from engineering through two governed AI experiences.

## Area A — Engineering and governed data flow

**Show:** the architecture diagram, then run the prepared Databricks job.

1. Point out synthetic CAD and hospital data in Fabric OneLake landing.
2. Explain that Databricks reads this landing zone through **read-only OneLake catalog federation**.
3. Start a full refresh of the preconfigured `av-demo-pipeline` Lakeflow
   Declarative Pipeline.
4. Show the successful run summary and the two deterministic exceptions: one duplicate CAD event and one handover completed before arrival.
5. Show the four approved gold objects: `fact_case`, `dim_region`, `dim_hospital`, `operational_metrics`.
6. Explain that approved gold objects are mirrored back to Fabric; Databricks does not write transformations to the landing zone.
7. Show that person and crew hashes are not present in gold or the mirror.

Say:

> The governance boundary is the gold contract. The same approved definitions feed Fabric and Genie, while direct identifiers are physically excluded.

**Recovery:** If the job or a catalog view does not load, use the last successful run, architecture diagram and pre-captured object-list screenshot. Do not reconfigure federation or mirroring live.

## Area B — Analyst experience with Databricks Genie

**Show:** the pre-staged Genie space restricted to approved gold objects.

Ask:

> For 15 September 2026 as at 12:00 UTC, summarise active and completed cases by region.

Then ask:

> Which hospitals have the most handovers over 40 minutes, and what is their average handover time?

Verify that the response:

- references the fixed snapshot;
- uses only approved gold objects;
- distinguishes counts from averages;
- avoids clinical or staffing recommendations.

Say:

> Genie provides an analyst-oriented route to the governed gold layer. Its answer is checked against the same certified totals used by Power BI.

**Recovery:** If Genie is unavailable or returns an unsuitable answer, show the saved successful result, state when it was captured, and compare its values with the prepared report. Do not improvise a prompt about patients, crews or clinical outcomes.

## Area C — Power BI Direct Lake and Copilot

**Show:** the prepared overview page and semantic model fields.

1. Point out Direct Lake mode over the mirrored gold objects.
2. Show cards for:
   - Active Cases
   - Completed Cases
   - Average Mobilisation Minutes
   - Average Hospital Handover Minutes
   - Handovers Over 40 Minutes
   - Data Quality Exceptions
3. Show a region breakdown and a hospital handover visual.
4. Open Copilot and ask:

> Summarise ambulance operations for 15 September 2026 as at 12:00 UTC. Focus on active and completed cases, mobilisation time, hospital handover time and data quality exceptions.

5. Ask:

> Identify hospitals with handovers over 40 minutes. Describe the operational pattern without recommending clinical action.

Say:

> Direct Lake keeps the presentation path simple, while model descriptions and Copilot instructions anchor the narrative to certified measures.

**Recovery:** If Copilot is unavailable, use the prepared narrative visual or screenshot and read the certified measures directly from the report. If Direct Lake falls back or shows an error, use the pre-captured report page and disclose that it represents the fixed snapshot.

## Area D — Guardrails and close

**Show:** the guardrail summary in the architecture and the semantic model field list.

Confirm:

- synthetic data and fixed as-of labelling;
- read-only federation into Databricks;
- approved gold-only consumption;
- physical exclusion of `patient_id_hash` and `crew_id_hash`;
- access limited to the approved demonstration group;
- AI output verified against certified measures;
- no clinical advice, patient conclusions or staff performance ranking.

Close with:

> One governed operational contract serves engineers, analysts and report consumers. The AI experiences improve discovery and explanation; certified measures and human review remain the authority.

## Full-demo recovery

If network or portal access is lost:

1. Continue from the architecture diagram.
2. Use the pre-captured engineering object list.
3. Use the exported six-measure summary.
4. Show saved Genie and Copilot outputs, clearly labelled with capture time.
5. State that all material represents the fixed `2026-09-15T12:00:00Z` snapshot.
6. Do not attempt credentials, permissions, pipeline runs or configuration changes in front of the audience.
