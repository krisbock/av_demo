-- Bind :catalog to the dedicated demonstration catalog.
CREATE CATALOG IF NOT EXISTS IDENTIFIER(:catalog);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:silver_schema);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:gold_schema);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:ops_schema);

