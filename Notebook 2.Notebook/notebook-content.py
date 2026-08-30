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

%pip install gtfs-realtime-bindings


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
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
