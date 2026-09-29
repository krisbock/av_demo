# Databricks notebook source
"""Prepared operational queries used as a non-AI recovery path."""

from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "av_demo")
catalog = dbutils.widgets.get("catalog")

display(
    spark.read.table(f"{catalog}.gold.fact_case")
    .groupBy("region_code")
    .agg(F.sum(F.col("active_flag").cast("long")).alias("active_cases"))
    .orderBy("region_code")
)
display(
    spark.read.table(f"{catalog}.gold.fact_case")
    .where(F.col("synthetic_hospital_name").isNotNull())
    .groupBy("synthetic_hospital_name")
    .agg(
        F.round(F.avg("hospital_handover_minutes"), 2).alias(
            "average_hospital_handover_minutes"
        )
    )
    .orderBy("average_hospital_handover_minutes", ascending=False)
)
