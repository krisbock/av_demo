-- Q1: How many active cases are there by region for 15 September 2026?
SELECT region_code, active_cases
FROM av_demo.gold.active_cases_by_region
ORDER BY region_code;

-- Q2: Which synthetic hospitals had the highest average handover time?
SELECT synthetic_hospital_name, average_hospital_handover_minutes
FROM av_demo.gold.handover_by_hospital
ORDER BY average_hospital_handover_minutes DESC;

-- Q3: How many handovers exceeded 40 minutes?
SELECT handovers_over_40_minutes
FROM av_demo.gold.operational_metrics
WHERE reporting_date = DATE '2026-09-15';

