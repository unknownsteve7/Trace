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

# ── Config ──────────────────────────────────────────────────────────
# The OTD API key is read from Azure Key Vault, never from source.
# One-time setup: create a Key Vault, add a secret named "otd-api-key",
# and grant the workspace identity / pipeline owner "Get" on secrets.
KEY_VAULT_URL   = "https://trace-kv.vault.azure.net/"   # <-- set to your vault
OTD_SECRET_NAME = "otd-api-key"

# GPS sanity limits for derived speed (see docs/bugs_and_known_issues.md BUG-001)
MAX_BUS_SPEED_KMH = 120.0
# Delhi NCR bounding box — pings outside it are GPS glitches
LAT_MIN, LAT_MAX = 28.0, 29.2
LON_MIN, LON_MAX = 76.5, 77.8

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Bronze: append raw positions (append-only, never rewritten) ─────
import requests
from datetime import datetime, timezone, timedelta
from google.transit import gtfs_realtime_pb2
from pyspark.sql import Row

API_KEY = notebookutils.credentials.getSecret(KEY_VAULT_URL, OTD_SECRET_NAME)
IST = timezone(timedelta(hours=5, minutes=30))

url = "https://otd.delhi.gov.in/api/realtime/VehiclePositions.pb"
response = requests.get(url, params={"key": API_KEY}, timeout=30)
response.raise_for_status()

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

if not rows:
    raise RuntimeError("OTD feed returned no vehicle positions — check API key / feed status")

df = spark.createDataFrame(rows)
df.write.format("delta").mode("append").saveAsTable("bronze_vehicle_positions")
print(f"Appended {len(rows)} vehicle positions")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Silver: derived speed, computed incrementally ───────────────────
# Only this run's Bronze rows are processed. Each vehicle's latest
# Silver ping is unioned in so the lag() window has a predecessor;
# those context rows are dropped before appending.
from pyspark.sql import Window
from pyspark.sql.functions import (
    col, lag, lit, when, to_timestamp, row_number,
    max as spark_max, round as spark_round
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

SILVER_TABLE = "silver_vehicle_positions"
silver_exists = spark.catalog.tableExists(SILVER_TABLE)

bronze_cols = ["entity_id", "vehicle_id", "trip_id", "route_id", "latitude",
               "longitude", "speed", "timestamp", "status", "ingested_at"]

bronze = spark.table("bronze_vehicle_positions").select(*bronze_cols)
if silver_exists:
    # First run after deploy backfills all Bronze; afterwards only new rows
    watermark = (spark.table(SILVER_TABLE)
                 .agg(spark_max(to_timestamp(col("ingested_at")))).first()[0])
    new_rows = (bronze.filter(to_timestamp(col("ingested_at")) > lit(watermark))
                if watermark else bronze)
else:
    new_rows = bronze

# BUG-001: drop (0,0) fallbacks and pings outside Delhi NCR
new_rows = new_rows.filter(
    col("latitude").between(LAT_MIN, LAT_MAX) &
    col("longitude").between(LON_MIN, LON_MAX)
).dropDuplicates(["vehicle_id", "timestamp"]).withColumn("_is_new", lit(True))

if silver_exists:
    last_w = Window.partitionBy("vehicle_id").orderBy(to_timestamp(col("timestamp")).desc())
    context = (spark.table(SILVER_TABLE).select(*bronze_cols)
               .withColumn("_rn", row_number().over(last_w))
               .filter(col("_rn") == 1).drop("_rn")
               .withColumn("_is_new", lit(False)))
    work = new_rows.unionByName(context)
else:
    work = new_rows

# BUG-002: parse the full ISO string including +05:30, so the instant is
# exact regardless of the Spark session time zone. The original IST
# string column is kept for the warehouse (hour-of-day = local time).
work = work.withColumn("event_ts", to_timestamp(col("timestamp")))

w = Window.partitionBy("vehicle_id").orderBy("event_ts")
positions_with_speed = (work
    .withColumn("prev_lat", lag("latitude").over(w))
    .withColumn("prev_lon", lag("longitude").over(w))
    .withColumn("prev_ts",  lag("event_ts").over(w))
    .withColumn("dist_km", haversine_km(
        col("prev_lat"), col("prev_lon"),
        col("latitude"),  col("longitude")
    ))
    .withColumn("time_diff_hrs",
        (col("event_ts").cast("long") - col("prev_ts").cast("long")) / 3600.0
    )
    .withColumn("raw_speed_kmh",
        when((col("time_diff_hrs") > 0) & col("dist_km").isNotNull(),
             col("dist_km") / col("time_diff_hrs"))
    )
    .withColumn("derived_speed_kmh",
        # NULL (unknown) rather than 0 for first pings and GPS jumps
        when(col("raw_speed_kmh") <= MAX_BUS_SPEED_KMH,
             spark_round(col("raw_speed_kmh"), 2))
    )
    .filter(col("_is_new"))
)

glitches = positions_with_speed.filter(col("raw_speed_kmh") > MAX_BUS_SPEED_KMH).count()

(positions_with_speed
    .select(*bronze_cols, "derived_speed_kmh")
    .write.format("delta").mode("append").saveAsTable(SILVER_TABLE))

print(f"Silver: appended {new_rows.count()} rows, nulled {glitches} speed glitches > {MAX_BUS_SPEED_KMH} km/h")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
