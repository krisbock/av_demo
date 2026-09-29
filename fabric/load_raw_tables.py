# Fabric notebook source
"""Load uploaded synthetic fixture files into Fabric Lakehouse Delta tables."""

from pyspark.sql import functions as F

spark.sql("CREATE SCHEMA IF NOT EXISTS raw_av")

cad_events = (
    spark.read.json("Files/raw_av/cad_events/*.jsonl")
    .withColumn("event_timestamp_utc", F.to_timestamp("event_timestamp_utc"))
    .withColumn("ingestion_timestamp_utc", F.to_timestamp("ingestion_timestamp_utc"))
)
hospital_arrivals = (
    spark.read.option("header", True)
    .csv("Files/raw_av/hospital_arrivals/*.csv")
    .withColumn("arrival_timestamp_utc", F.to_timestamp("arrival_timestamp_utc"))
    .withColumn(
        "handover_complete_timestamp_utc",
        F.to_timestamp("handover_complete_timestamp_utc"),
    )
)

cad_events.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    "raw_av.cad_events"
)
hospital_arrivals.write.mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("raw_av.hospital_arrivals")

display(
    spark.createDataFrame(
        (
            ("raw_av.cad_events", cad_events.count()),
            ("raw_av.hospital_arrivals", hospital_arrivals.count()),
        ),
        "table_name string, row_count long",
    )
)
