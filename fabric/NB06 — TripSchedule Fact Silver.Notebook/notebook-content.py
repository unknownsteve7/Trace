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



from pyspark.sql.functions import (
    col, split, udf, expr, trim
)
from pyspark.sql.types import IntegerType

@udf(returnType=IntegerType())
def gtfs_time_to_seconds(t):
    """Convert GTFS HH:MM:SS (can be >24h) to seconds from midnight."""
    if t is None:
        return None
    parts = t.strip().split(":")
    if len(parts) != 3:
        return None
    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    return h * 3600 + m * 60 + s

bronze_st = spark.table("bronze_stop_times")

print("bronze_stop_times schema:")
bronze_st.printSchema()
print(f"Total rows: {bronze_st.count():,}")
display(bronze_st.limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col, when, floor

fact_schedule = bronze_st.select(
    col("trip_id"),
    col("stop_id"),
    col("stop_sequence").cast("int"),
    col("arrival_time"),
    col("departure_time"),
    gtfs_time_to_seconds(col("arrival_time")).alias("arrival_secs"),
    gtfs_time_to_seconds(col("departure_time")).alias("departure_secs"),
)

# Derive departure hour from seconds
fact_schedule = fact_schedule.withColumn(
    "departure_hour",
    (col("departure_secs") / 3600).cast("int")
).withColumn(
    "is_peak_hour",
    when(
        (col("departure_hour").between(7, 9)) |
        (col("departure_hour").between(17, 19)),
        1
    ).otherwise(0)
)

fact_schedule.write.format("delta").mode("overwrite").saveAsTable("silver_fact_schedule")
print(f"Fact_TripSchedule — {fact_schedule.count():,} rows")
display(fact_schedule.limit(10))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

spark.sql("""
    SELECT
        is_peak_hour,
        COUNT(*) as stop_events,
        COUNT(DISTINCT trip_id) as trips
    FROM silver_fact_schedule
    GROUP BY is_peak_hour
    ORDER BY is_peak_hour
""").show()


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
