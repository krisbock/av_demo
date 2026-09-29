-- Group names are synthetic examples. Run as the Unity Catalog owner.
GRANT USE CATALOG ON CATALOG av_demo TO `av_demo_engineer`;
GRANT USE SCHEMA, SELECT ON SCHEMA av_demo.silver TO `av_demo_engineer`;
GRANT USE SCHEMA, SELECT ON SCHEMA av_demo.gold TO `av_demo_engineer`;
GRANT USE SCHEMA ON SCHEMA av_demo.gold TO `av_demo_analyst`;
GRANT SELECT ON VIEW av_demo.gold.active_cases_by_region TO `av_demo_analyst`;
GRANT SELECT ON VIEW av_demo.gold.handover_by_hospital TO `av_demo_analyst`;
GRANT SELECT ON TABLE av_demo.gold.operational_metrics TO `av_demo_analyst`;

