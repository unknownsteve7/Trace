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

from pyspark.sql.functions import col, trim, regexp_replace

bronze_routes = spark.table("bronze_routes")

dim_route = bronze_routes.select(
    col("route_id"),
    trim(col("route_short_name")).alias("route_short_name"),
    trim(col("route_long_name")).alias("route_long_name"),
    col("route_type").cast("int")
).dropDuplicates(["route_id"])

dim_route.write.format("delta").mode("overwrite").saveAsTable("silver_dim_route")
print(f"Dim_Route — {dim_route.count()} rows")
display(dim_route.limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import (
    explode, sequence, to_date, lit,
    year, month, dayofmonth, dayofweek,
    date_format, quarter, weekofyear
)

date_range = spark.sql("""
    SELECT explode(sequence(
        to_date('2024-01-01'),
        to_date('2026-12-31'),
        interval 1 day
    )) AS date
""")

dim_date = date_range.select(
    date_format(col("date"), "yyyyMMdd").cast("int").alias("date_key"),
    col("date"),
    year("date").alias("year"),
    quarter("date").alias("quarter"),
    month("date").alias("month"),
    date_format(col("date"), "MMMM").alias("month_name"),
    weekofyear("date").alias("week_of_year"),
    dayofmonth("date").alias("day_of_month"),
    dayofweek("date").alias("day_of_week"),       # 1=Sun, 7=Sat
    date_format(col("date"), "EEEE").alias("day_name"),
    (dayofweek("date").isin([1, 7])).cast("int").alias("is_weekend"),
    # Delhi public holidays (major ones) — extend as needed
    col("date").isin([
        "2024-01-26", "2024-08-15", "2024-10-02",  # Republic, Independence, Gandhi
        "2025-01-26", "2025-08-15", "2025-10-02",
        "2026-01-26", "2026-08-15", "2026-10-02",
    ]).cast("int").alias("is_public_holiday")
)

dim_date.write.format("delta").mode("overwrite").saveAsTable("silver_dim_date")
print(f"Dim_Date — {dim_date.count()} rows")
display(dim_date.limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

bronze_trips = spark.table("bronze_trips")
bronze_cal   = spark.table("bronze_calendar")

print("bronze_trips columns:", bronze_trips.columns)
print("bronze_calendar columns:", bronze_cal.columns)

dim_trip = bronze_trips.join(bronze_cal, on="service_id", how="left").select(
    col("trip_id"),
    col("route_id"),
    col("service_id"),
    col("shape_id"),          
    col("monday").cast("int"),
    col("tuesday").cast("int"),
    col("wednesday").cast("int"),
    col("thursday").cast("int"),
    col("friday").cast("int"),
    col("saturday").cast("int"),
    col("sunday").cast("int"),
    col("start_date"),
    col("end_date")
).dropDuplicates(["trip_id"])

dim_trip.write.format("delta").mode("overwrite").saveAsTable("silver_dim_trip")
print(f"Dim_Trip — {dim_trip.count()} rows")
display(dim_trip.limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

bronze_stops = spark.table("bronze_stops")

dim_stop = bronze_stops.select(
    col("stop_id"),
    trim(col("stop_name")).alias("stop_name"),
    col("stop_lat").cast("double"),
    col("stop_lon").cast("double")
).dropDuplicates(["stop_id"])

dim_stop.write.format("delta").mode("overwrite").saveAsTable("silver_dim_stop")
print(f"Dim_Stop — {dim_stop.count()} rows")
display(dim_stop.limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
