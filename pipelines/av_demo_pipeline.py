# Databricks notebook source
"""Lakeflow Declarative Pipeline for the fixed Ambulance Victoria demo snapshot."""

import re

from pyspark import pipelines as dp
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def _configuration_identifier(name: str, default: str) -> str:
    """Return a validated Unity Catalog identifier from pipeline configuration."""
    value = spark.conf.get(name, default)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid Unity Catalog identifier configured for {name}: {value}")
    return value


catalog = _configuration_identifier("av_demo.catalog", "av_demo")
raw_catalog = _configuration_identifier(
    "av_demo.raw_catalog",
    "replace_with_onelake_foreign_catalog",
)
raw_schema = _configuration_identifier("av_demo.raw_schema", "raw_av")
as_of_timestamp_utc = spark.conf.get(
    "av_demo.as_of_timestamp_utc",
    "2026-09-15T12:00:00Z",
)


def _output_table(schema: str, table: str) -> str:
    """Return a fully qualified pipeline output table name."""
    return f"{catalog}.{schema}.{table}"


@dp.materialized_view(
    name="_ranked_case_events",
    private=True,
    comment="Private ranked CAD events used for deduplication.",
)
def ranked_case_events() -> DataFrame:
    """Parse source timestamps and rank duplicate OneLake CAD events."""
    duplicate_window = Window.partitionBy("event_id").orderBy(
        F.col("ingestion_timestamp_utc"),
        F.col("event_timestamp_utc"),
    )
    return (
        spark.read.table(f"{raw_catalog}.{raw_schema}.cad_events")
        .withColumn("event_timestamp_utc", F.to_timestamp("event_timestamp_utc"))
        .withColumn(
            "ingestion_timestamp_utc",
            F.to_timestamp("ingestion_timestamp_utc"),
        )
        .withColumn("_duplicate_rank", F.row_number().over(duplicate_window))
    )


@dp.materialized_view(
    name="_parsed_hospital_arrivals",
    private=True,
    comment="Private parsed hospital arrivals used for validation.",
)
def parsed_hospital_arrivals() -> DataFrame:
    """Parse source timestamps from the OneLake hospital-arrival table."""
    return (
        spark.read.table(f"{raw_catalog}.{raw_schema}.hospital_arrivals")
        .withColumn("arrival_timestamp_utc", F.to_timestamp("arrival_timestamp_utc"))
        .withColumn(
            "handover_complete_timestamp_utc",
            F.to_timestamp("handover_complete_timestamp_utc"),
        )
    )


@dp.materialized_view(
    name="_accepted_case_events",
    private=True,
    comment="Private accepted CAD events after duplicate rejection.",
)
@dp.expect_or_drop("unique_cad_event_identifier", "_duplicate_rank = 1")
def accepted_case_events() -> DataFrame:
    """Apply the duplicate-event expectation before removing helper columns."""
    return spark.read.table("_ranked_case_events")


@dp.materialized_view(
    name=_output_table("silver", "case_events"),
    comment="Deduplicated synthetic CAD events from the read-only OneLake source.",
)
def case_events() -> DataFrame:
    """Publish one accepted row for each CAD event identifier."""
    return spark.read.table("_accepted_case_events").withColumn(
        "processing_timestamp_utc",
        F.current_timestamp(),
    ).drop("_duplicate_rank")


@dp.materialized_view(
    name=_output_table("silver", "hospital_handovers"),
    comment="Validated synthetic hospital handovers from the read-only OneLake source.",
)
@dp.expect_or_drop(
    "handover_completion_follows_arrival",
    "handover_complete_timestamp_utc >= arrival_timestamp_utc",
)
def hospital_handovers() -> DataFrame:
    """Publish valid handovers with their elapsed duration."""
    return (
        spark.read.table("_parsed_hospital_arrivals")
        .withColumn(
            "hospital_handover_minutes",
            (
                F.unix_timestamp("handover_complete_timestamp_utc")
                - F.unix_timestamp("arrival_timestamp_utc")
            )
            / F.lit(60),
        )
        .withColumn("processing_timestamp_utc", F.current_timestamp())
    )


@dp.materialized_view(
    name=_output_table("silver", "data_quality_results"),
    comment="Rows rejected by the two controlled demonstration quality rules.",
)
def data_quality_results() -> DataFrame:
    """Publish duplicate-event and invalid-handover quality exceptions."""
    duplicate_results = (
        spark.read.table("_ranked_case_events")
        .filter(F.col("_duplicate_rank") > 1)
        .select(
            F.lit("DQ-001").alias("rule_id"),
            F.lit("Unique CAD event identifier").alias("rule_name"),
            F.lit("cad_events").alias("dataset_name"),
            F.col("event_id").alias("record_identifier"),
            F.lit("HIGH").alias("severity"),
            F.col("event_id").alias("observed_value"),
            F.lit("event_id must be unique").alias("expected_condition"),
        )
    )
    arrival_results = (
        spark.read.table("_parsed_hospital_arrivals")
        .filter(
            F.col("handover_complete_timestamp_utc")
            < F.col("arrival_timestamp_utc")
        )
        .select(
            F.lit("DQ-002").alias("rule_id"),
            F.lit("Handover completion follows arrival").alias("rule_name"),
            F.lit("hospital_arrivals").alias("dataset_name"),
            F.col("case_id").alias("record_identifier"),
            F.lit("CRITICAL").alias("severity"),
            F.col("handover_complete_timestamp_utc")
            .cast("string")
            .alias("observed_value"),
            F.lit(
                "handover_complete_timestamp_utc >= arrival_timestamp_utc"
            ).alias("expected_condition"),
        )
    )
    return duplicate_results.unionByName(arrival_results).withColumn(
        "detected_timestamp_utc",
        F.current_timestamp(),
    )


@dp.materialized_view(
    name=_output_table("gold", "fact_case"),
    comment="One governed synthetic case row at the configured reporting snapshot.",
)
def fact_case() -> DataFrame:
    """Reconstruct case lifecycle facts at the configured as-of timestamp."""
    as_of = F.to_timestamp(F.lit(as_of_timestamp_utc))
    snapshot_events = spark.read.table(
        _output_table("silver", "case_events")
    ).filter(F.col("event_timestamp_utc") <= as_of)
    snapshot_handovers = spark.read.table(
        _output_table("silver", "hospital_handovers")
    ).filter(
        (F.col("arrival_timestamp_utc") <= as_of)
        & (F.col("handover_complete_timestamp_utc") <= as_of)
    )
    case_lifecycle = snapshot_events.groupBy("case_id").agg(
        F.first("region_code", ignorenulls=True).alias("region_code"),
        F.first("case_priority", ignorenulls=True).alias("case_priority"),
        F.min(
            F.when(
                F.col("event_type") == "CASE_CREATED",
                F.col("event_timestamp_utc"),
            )
        ).alias("created_timestamp_utc"),
        F.min(
            F.when(
                F.col("event_type") == "UNIT_DISPATCHED",
                F.col("event_timestamp_utc"),
            )
        ).alias("dispatch_timestamp_utc"),
        F.min(
            F.when(
                F.col("event_type") == "UNIT_CLEARED",
                F.col("event_timestamp_utc"),
            )
        ).alias("clear_timestamp_utc"),
    )
    handovers = snapshot_handovers.select(
        "case_id",
        "synthetic_hospital_name",
        "hospital_handover_minutes",
    )
    return (
        case_lifecycle.join(handovers, "case_id", "left")
        .withColumn(
            "mobilisation_minutes",
            (
                F.unix_timestamp("dispatch_timestamp_utc")
                - F.unix_timestamp("created_timestamp_utc")
            )
            / F.lit(60),
        )
        .withColumn("active_flag", F.col("clear_timestamp_utc").isNull())
        .withColumn(
            "lifecycle_complete_flag",
            F.col("clear_timestamp_utc").isNotNull(),
        )
    )


@dp.materialized_view(
    name=_output_table("gold", "dim_region"),
    comment="Regions represented in the governed case fact.",
)
def dim_region() -> DataFrame:
    """Publish the distinct synthetic region dimension."""
    return spark.read.table(_output_table("gold", "fact_case")).select(
        "region_code"
    ).distinct()


@dp.materialized_view(
    name=_output_table("gold", "dim_hospital"),
    comment="Synthetic hospitals represented in the governed case fact.",
)
def dim_hospital() -> DataFrame:
    """Publish the distinct synthetic hospital dimension."""
    return (
        spark.read.table(_output_table("gold", "fact_case"))
        .select("synthetic_hospital_name")
        .where(F.col("synthetic_hospital_name").isNotNull())
        .distinct()
    )


@dp.materialized_view(
    name=_output_table("gold", "operational_metrics"),
    comment="Certified fixed-snapshot operational measures for the demo.",
)
def operational_metrics() -> DataFrame:
    """Publish the six certified aggregate demonstration measures."""
    facts = spark.read.table(_output_table("gold", "fact_case"))
    exceptions = spark.read.table(
        _output_table("silver", "data_quality_results")
    ).agg(F.count(F.lit(1)).alias("data_quality_exceptions"))
    return (
        facts.agg(
            F.sum(F.col("active_flag").cast("long")).alias("active_cases"),
            F.sum(F.col("lifecycle_complete_flag").cast("long")).alias(
                "completed_cases"
            ),
            F.round(F.avg("mobilisation_minutes"), 2).alias(
                "average_mobilisation_minutes"
            ),
            F.round(F.avg("hospital_handover_minutes"), 2).alias(
                "average_hospital_handover_minutes"
            ),
            F.sum((F.col("hospital_handover_minutes") > 40).cast("long")).alias(
                "handovers_over_40_minutes"
            ),
        )
        .crossJoin(exceptions)
        .withColumn("reporting_date", F.to_date(F.lit(as_of_timestamp_utc)))
    )


@dp.materialized_view(
    name=_output_table("ops", "pipeline_run_log"),
    comment="Current Lakeflow pipeline refresh summary for the fixed demo snapshot.",
)
def pipeline_run_log() -> DataFrame:
    """Publish a refresh summary derived from the current pipeline outputs."""
    source_count = (
        spark.read.table(f"{raw_catalog}.{raw_schema}.cad_events")
        .agg(F.count(F.lit(1)).alias("cad_count"))
        .crossJoin(
            spark.read.table(f"{raw_catalog}.{raw_schema}.hospital_arrivals").agg(
                F.count(F.lit(1)).alias("arrival_count")
            )
        )
        .select((F.col("cad_count") + F.col("arrival_count")).alias("source_record_count"))
    )
    exception_count = spark.read.table(
        _output_table("silver", "data_quality_results")
    ).agg(F.count(F.lit(1)).alias("quarantined_record_count"))
    return (
        source_count.crossJoin(exception_count)
        .withColumn("pipeline_name", F.lit("av_demo_pipeline"))
        .withColumn("refresh_timestamp_utc", F.current_timestamp())
        .withColumn(
            "status",
            F.when(
                F.col("quarantined_record_count") > 0,
                F.lit("SUCCESS_WITH_WARNINGS"),
            ).otherwise(F.lit("SUCCESS")),
        )
        .withColumn(
            "accepted_record_count",
            F.col("source_record_count") - F.col("quarantined_record_count"),
        )
        .select(
            "pipeline_name",
            "refresh_timestamp_utc",
            "status",
            "source_record_count",
            "accepted_record_count",
            "quarantined_record_count",
        )
    )
