# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "33b6062c-9c34-4c28-a37f-86a9ce3bebb7",
# META       "default_lakehouse_name": "trace_lakehouse",
# META       "default_lakehouse_workspace_id": "d41e9c81-c1d3-4306-aec1-ca3a5283795b",
# META       "known_lakehouses": [
# META         {
# META           "id": "33b6062c-9c34-4c28-a37f-86a9ce3bebb7"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# ── Data quality checks for the Silver layer ────────────────────────
# Run after NB01–NB07 (and before EXEC dbo.usp_load_warehouse).
# Every check is recorded; the notebook fails at the end if any
# ERROR-level check failed, so a pipeline run goes red instead of
# silently loading bad data.
from datetime import datetime, timedelta, timezone
from pyspark.sql.functions import (
    col, count, countDistinct, current_timestamp, unix_timestamp,
    max as spark_max, to_timestamp
)

IST = timezone(timedelta(hours=5, minutes=30))
MAX_BUS_SPEED_KMH = 120.0
FRESHNESS_MINUTES = 30

results = []

def check(name, passed, detail="", level="ERROR"):
    results.append((level, name, bool(passed), detail))

def key_checks(table, key):
    df = spark.table(table)
    stats = df.agg(count("*").alias("n"),
                   count(col(key)).alias("non_null"),
                   countDistinct(col(key)).alias("distinct")).first()
    check(f"{table}: not empty", stats.n > 0, f"{stats.n} rows")
    check(f"{table}: {key} not null", stats.non_null == stats.n, f"{stats.n - stats.non_null} nulls")
    check(f"{table}: {key} unique", stats.distinct == stats.non_null,
          f"{stats.non_null - stats.distinct} duplicates")

def orphan_check(fact, fk, dim, pk, level="ERROR"):
    orphans = (spark.table(fact).select(fk).distinct()
               .join(spark.table(dim).select(col(pk).alias(fk)), on=fk, how="left_anti")
               .count())
    check(f"{fact}.{fk} -> {dim}.{pk}", orphans == 0, f"{orphans} orphan keys", level)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Dimensions ───────────────────────────────────────────────────────
key_checks("silver_dim_route", "route_id")
key_checks("silver_dim_stop",  "stop_id")
key_checks("silver_dim_trip",  "trip_id")
key_checks("silver_dim_date",  "date")

today = datetime.now(IST).date()
max_date = spark.table("silver_dim_date").agg(spark_max("date")).first()[0]
check("silver_dim_date: covers next 90 days", max_date >= today + timedelta(days=90),
      f"max date {max_date}", level="WARN")

stops_out = spark.table("silver_dim_stop").filter(
    ~col("stop_lat").between(28.0, 29.2) | ~col("stop_lon").between(76.5, 77.8)).count()
check("silver_dim_stop: coordinates in Delhi NCR", stops_out == 0, f"{stops_out} stops outside", level="WARN")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Facts ────────────────────────────────────────────────────────────
orphan_check("silver_dim_trip", "route_id", "silver_dim_route", "route_id")
orphan_check("silver_fact_schedule", "trip_id", "silver_dim_trip", "trip_id")
orphan_check("silver_fact_schedule", "stop_id", "silver_dim_stop", "stop_id")

bad_hours = spark.table("silver_fact_schedule").filter(
    col("departure_hour").isNull() | (col("departure_hour") < 0) | (col("departure_hour") > 30)).count()
check("silver_fact_schedule: departure_hour in 0..30", bad_hours == 0, f"{bad_hours} bad rows")

key_checks("silver_fact_weather", "date")

if spark.catalog.tableExists("silver_vehicle_positions"):
    vp = spark.table("silver_vehicle_positions")
    too_fast = vp.filter(col("derived_speed_kmh") > MAX_BUS_SPEED_KMH).count()
    check("silver_vehicle_positions: speed <= 120 km/h", too_fast == 0, f"{too_fast} rows")

    off_map = vp.filter(~col("latitude").between(28.0, 29.2) | ~col("longitude").between(76.5, 77.8)).count()
    check("silver_vehicle_positions: coordinates in Delhi NCR", off_map == 0, f"{off_map} rows")

    # Age computed inside Spark so driver vs. session time zones can't skew it
    last, age_min = vp.agg(
        spark_max(to_timestamp(col("ingested_at"))).alias("last"),
        ((unix_timestamp(current_timestamp())
          - unix_timestamp(spark_max(to_timestamp(col("ingested_at"))))) / 60).alias("age_min")
    ).first()
    check(f"silver_vehicle_positions: fresh (< {FRESHNESS_MINUTES} min)",
          age_min is not None and age_min < FRESHNESS_MINUTES,
          f"last ingest {last}", level="WARN")

    orphan_check("silver_vehicle_positions", "route_id", "silver_dim_route", "route_id", level="WARN")
else:
    check("silver_vehicle_positions exists", False, "run NB02 first")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Report ───────────────────────────────────────────────────────────
for level, name, passed, detail in results:
    print(f"{'PASS' if passed else level:5}  {name}  ({detail})")

failed = [name for level, name, passed, _ in results if not passed and level == "ERROR"]
warned = [name for level, name, passed, _ in results if not passed and level == "WARN"]
print(f"\n{len(results)} checks: {len(failed)} errors, {len(warned)} warnings")

if failed:
    raise AssertionError("Data quality checks failed: " + "; ".join(failed))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
