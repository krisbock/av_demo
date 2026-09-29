# Ambulance Victoria Databricks, Fabric and AI demo

This repository implements a compact, repeatable demonstration of Microsoft Fabric
and Azure Databricks as complementary data and AI platforms.

> **Synthetic data only.** Never populate this repository, its generated folders,
> configured OneLake paths or demonstration workspaces with production patient,
> employee, paramedic, vehicle or incident data.

The demonstration story is:

1. Synthetic CAD and hospital-arrival data lands once in a Fabric OneLake Lakehouse.
2. Azure Databricks reads that source through read-only OneLake catalog federation.
3. Databricks validates the source and writes managed Unity Catalog silver and gold
   Delta tables.
4. Databricks AI/BI Genie answers questions against approved gold objects.
5. Selected identifier-free gold objects are mirrored into Fabric.
6. A Direct Lake semantic model supplies the same governed measures to Power BI
   Copilot.

See [ARCHITECTURE.md](./ARCHITECTURE.md) and [DEMO_SCRIPT.md](./DEMO_SCRIPT.md)
for the platform design and presentation runbook.

## Demonstration scope

The fixed fixture contains:

- 200 synthetic cases;
- 10 fictional units;
- five explicitly synthetic hospitals;
- a fixed date of 15 September 2026;
- 40 active and 160 completed cases at the configured as-of timestamp;
- one duplicate CAD event;
- one hospital handover completed before arrival.

The controlled issue profile therefore produces exactly two quality exceptions.
No patient or crew identifier is generated.

## Prerequisites

### Local

- `uv`
- Python 3.11

### Azure Databricks

- A workspace enabled for Unity Catalog.
- Databricks CLI authenticated to the target workspace.
- Serverless Lakeflow Declarative Pipelines enabled in the target workspace.
- Permission to create the dedicated `av_demo` catalogue or its schemas.
- An existing, validated OneLake connection and foreign catalogue.

### Microsoft Fabric and Power BI

- A Fabric workspace and Lakehouse.
- Tenant settings and an authorised identity for OneLake access.
- A supported Fabric capacity for mirroring, Direct Lake and Copilot.
- Permission to create a mirrored Azure Databricks item and semantic model.

Fabric and Power BI portal configuration is intentionally pre-staged rather than
automated. Follow [fabric/setup.md](./fabric/setup.md).

## Local setup

```bash
cd ambulance-victoria/av-databricks-fabric-ai-demo
uv sync --python 3.11 --extra dev
cp .env.example .env
```

Do not commit `.env`. Replace only the placeholders needed for the target
environment.

Generate the deterministic local fixture:

```bash
uv run python -m av_demo.generate_demo_data \
  --config config/demo_config.example.yml
```

The output is written beneath `generated/raw_av/`, which is ignored by Git.
Upload:

- `generated/raw_av/cad_events/cad_events.jsonl`
- `generated/raw_av/hospital_arrivals/hospital_arrivals.csv`

to the matching OneLake raw folders, then run
[fabric/load_raw_tables.py](./fabric/load_raw_tables.py) as a Fabric notebook
using the manual procedure in [fabric/setup.md](./fabric/setup.md).

## Test and validate

```bash
uv run coverage run -m pytest
uv run coverage report
uv run python demo/validate_demo.py
```

Coverage must remain at or above 80 per cent.

The local validator checks:

- the deterministic case and quality counts;
- the absence of restricted identifiers from the approved Python model;
- required repository assets;
- reference SQL for verified questions;
- required Genie guardrails.

Cloud connectivity and portal configuration must be checked using the preflight
steps in [DEMO_SCRIPT.md](./DEMO_SCRIPT.md).

## Configure Databricks

1. Copy `config/demo_config.example.yml` if environment-specific values are needed.
2. Create the OneLake connection and foreign catalogue using the supported
   Databricks workflow for the target workspace.
3. Confirm the foreign catalogue exposes:
   - `<raw_catalog>.raw_av.cad_events`
   - `<raw_catalog>.raw_av.hospital_arrivals`
4. Run [sql/create_schemas.sql](./sql/create_schemas.sql) with parameters for
   `av_demo.silver`, `av_demo.gold` and `av_demo.ops`.
5. Authenticate the Databricks CLI.
6. Validate, deploy and refresh the Lakeflow Declarative Pipeline:

```bash
databricks bundle validate \
  --var="raw_catalog=<foreign_catalog_name>"
databricks bundle deploy -t demo \
  --var="raw_catalog=<foreign_catalog_name>"
databricks bundle run -t demo av_demo_pipeline
```

The pipeline reads the OneLake foreign tables without modifying them and
materialises:

- `av_demo.silver.case_events`
- `av_demo.silver.hospital_handovers`
- `av_demo.silver.data_quality_results`
- `av_demo.gold.fact_case`
- `av_demo.gold.dim_region`
- `av_demo.gold.dim_hospital`
- `av_demo.gold.operational_metrics`
- `av_demo.ops.pipeline_run_log`

Run the static SQL assets in [sql/](./sql/) to create approved views, apply
example grants and verify expected queries. The group names are demonstration
placeholders and must be mapped to target Microsoft Entra groups.

## Configure Genie

Create or configure a Genie space manually with only:

- `av_demo.gold.fact_case`
- `av_demo.gold.dim_region`
- `av_demo.gold.dim_hospital`
- `av_demo.gold.operational_metrics`
- `av_demo.gold.active_cases_by_region`
- `av_demo.gold.handover_by_hospital`

Use [config/genie_instructions.md](./config/genie_instructions.md) as its
instructions and [sql/verified_queries.sql](./sql/verified_queries.sql) as the
verified-query reference.

Do not attach raw, silver, quarantine or operational audit tables to the Genie
space.

## Configure Fabric and Power BI

Follow [fabric/setup.md](./fabric/setup.md) to:

1. Mirror only the approved gold objects.
2. Verify restricted hashes are physically absent.
3. Build the Direct Lake semantic model described in
   [fabric/semantic_model_spec.md](./fabric/semantic_model_spec.md).
4. Add [powerbi/measures.dax](./powerbi/measures.dax).
5. Apply [powerbi/copilot_instructions.md](./powerbi/copilot_instructions.md).
6. Validate the fixed values before enabling the presentation.

## Reset

Local generated files can be removed safely with:

```bash
uv run python demo/reset_demo.py
```

The reset refuses to run unless `demo_environment` is `true` and the configured
target is a child of the project's `generated/` directory.

Cloud reset is deliberately manual. Delete or truncate only dedicated `av_demo`
objects after confirming that the catalogue, schemas, mirror and workspace are
demonstration resources.

## Security controls

- OneLake federation is treated as read-only.
- Silver and gold are written to normal Unity Catalog managed storage.
- Genie receives approved gold objects only.
- `patient_id_hash` and `crew_id_hash` are physically absent from generated,
  gold and mirrored objects.
- Fabric and Power BI permissions must be configured independently; Unity
  Catalog grants must not be assumed to propagate through mirroring.
- Requests for individual employee identifiers or performance rankings must be
  refused and redirected to authorised aggregate analysis.
- All organisations, people, cases, units and hospitals are synthetic.

## Limitations

### Executable in this repository

- Deterministic synthetic-data generation.
- Quality checks and lifecycle calculations.
- Canonical metric calculations.
- Databricks bundle and Lakeflow Declarative Pipeline source.
- SQL views, example grants and verified queries.
- Local tests, validation and safe generated-data reset.

### Manual portal configuration

- OneLake connection and catalog federation.
- Unity Catalog-to-Fabric mirroring.
- Direct Lake semantic-model creation.
- Genie space configuration.
- Power BI Copilot configuration.
- Tenant settings, workspace roles and capacity selection.

### Environment-specific placeholders

Workspace IDs, Lakehouse IDs, catalogue names, Databricks host names, warehouse
IDs, identities and group names must be supplied for the target demonstration
environment. Product availability and required capacity or workspace settings
must be revalidated before each presentation.
