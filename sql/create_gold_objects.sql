-- These convenience views are approved for Genie, but are not part of the
-- four-object Fabric mirror contract.
CREATE OR REPLACE VIEW av_demo.gold.active_cases_by_region AS
SELECT
  region_code,
  COUNT_IF(active_flag) AS active_cases
FROM av_demo.gold.fact_case
GROUP BY region_code;

CREATE OR REPLACE VIEW av_demo.gold.handover_by_hospital AS
SELECT
  synthetic_hospital_name,
  ROUND(AVG(hospital_handover_minutes), 2) AS average_hospital_handover_minutes,
  COUNT_IF(hospital_handover_minutes > 40) AS handovers_over_40_minutes
FROM av_demo.gold.fact_case
WHERE synthetic_hospital_name IS NOT NULL
GROUP BY synthetic_hospital_name;
