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
# META     },
# META     "environment": {
# META       "environmentId": "5983a934-1200-8eaf-4727-197a0ba7d2af",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# CELL ********************

import requests
from datetime import datetime, timezone, timedelta
from google.transit import gtfs_realtime_pb2
from pyspark.sql import Row

API_KEY = "kV0HS8CSWr6NmORI1XIPRqXm62fujtio"  # move to Fabric Environment secret
IST = timezone(timedelta(hours=5, minutes=30))

url = "https://otd.delhi.gov.in/api/realtime/VehiclePositions.pb"
response = requests.get(url, params={"key": API_KEY}, timeout=30)

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

rows = []
for entity in feed.entity:
    if entity.HasField("vehicle"):
        v = entity.vehicle
        rows.append(Row(
            entity_id=entity.id,
            vehicle_id=v.vehicle.id,
            trip_id=v.trip.trip_id,
            route_id=v.trip.route_id,
            latitude=float(v.position.latitude),
            longitude=float(v.position.longitude),
            speed=float(v.position.speed),
            timestamp=str(datetime.fromtimestamp(v.timestamp, tz=IST)),
            status=int(v.current_status),
            ingested_at=str(datetime.now(IST))
        ))

df = spark.createDataFrame(rows)
df.write.format("delta").mode("append").saveAsTable("bronze_vehicle_positions")
print(f"Appended {len(rows)} vehicle positions")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Compute derived speed from position delta ──────────────────────
from pyspark.sql import Window
from pyspark.sql.functions import (
    col, lag, unix_timestamp, when,
    round as spark_round, regexp_replace
)
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType
import math

@udf(DoubleType())
def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))

positions = spark.table("bronze_vehicle_positions")

# ── FIX: strip +05:30 timezone offset before unix_timestamp() ──────
positions = positions.withColumn(
    "ts_clean",
    regexp_replace(col("timestamp"), r"\+\d{2}:\d{2}$", "")
)

w = Window.partitionBy("vehicle_id").orderBy("ts_clean")

positions_with_speed = positions \
    .withColumn("prev_lat",  lag("latitude").over(w)) \
    .withColumn("prev_lon",  lag("longitude").over(w)) \
    .withColumn("prev_ts",   lag("ts_clean").over(w)) \
    .withColumn("dist_km", haversine_km(
        col("prev_lat"), col("prev_lon"),
        col("latitude"),  col("longitude")
    )) \
    .withColumn("time_diff_hrs",
        (unix_timestamp("ts_clean") - unix_timestamp("prev_ts")) / 3600.0
    ) \
    .withColumn("derived_speed_kmh",
        when(
            (col("time_diff_hrs") > 0) & (col("dist_km").isNotNull()),
            spark_round(col("dist_km") / col("time_diff_hrs"), 2)
        ).otherwise(0.0)
    ) \
    .drop("prev_lat", "prev_lon", "prev_ts", "dist_km", "time_diff_hrs", "ts_clean")

positions_with_speed.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("bronze_vehicle_positions")

print("Derived speeds computed")

# Show sample of moving vehicles
positions_with_speed.select("vehicle_id", "timestamp", "derived_speed_kmh") \
    .filter(col("derived_speed_kmh") > 0) \
    .orderBy(col("derived_speed_kmh").desc()) \
    .show(10)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
