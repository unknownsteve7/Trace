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


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pandas as pd

gtfs_files = [
    ("bronze_routes",     "routes.csv"),
    ("bronze_stops",      "stops.csv"),
    ("bronze_trips",      "trips.csv"),
    ("bronze_stop_times", "stop_times.csv"),
    ("bronze_calendar",   "calendar.csv"),
    ("bronze_agency",     "agency.csv"),
]

for table_name, filename in gtfs_files:
    df = spark.read.option("header", True).option("inferSchema", True).csv(f"Files/{filename}")
    df.write.format("delta").mode("overwrite").saveAsTable(table_name)
    print(f"{table_name} — {df.count()} rows")


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

# CELL ********************


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

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
