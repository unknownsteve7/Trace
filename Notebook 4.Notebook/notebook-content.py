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
from pyspark.sql import SparkSession


fuel_records = [
    ("2024-01-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-02-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-03-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-04-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-05-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-06-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-07-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-08-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-09-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-10-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-11-01", 94.72, 87.62, "Pre-revision price"),
    ("2024-12-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-01-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-02-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-03-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-04-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-05-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-06-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-07-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-08-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-09-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-10-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-11-01", 94.72, 87.62, "Pre-revision price"),
    ("2025-12-01", 94.72, 87.62, "Pre-revision price"),
    # 2026 — verified current prices from IOCL SMS (30-Aug-2026)
    ("2026-01-01", 102.12, 95.20, "IOCL verified"),
    ("2026-02-01", 102.12, 95.20, "IOCL verified"),
    ("2026-03-01", 102.12, 95.20, "IOCL verified"),
    ("2026-04-01", 102.12, 95.20, "IOCL verified"),
    ("2026-05-01", 102.12, 95.20, "IOCL verified"),
    ("2026-06-01", 102.12, 95.20, "IOCL verified"),
    ("2026-07-01", 102.12, 95.20, "IOCL verified"),
    ("2026-08-01", 102.12, 95.20, "IOCL verified"),
]

df_pd = pd.DataFrame(fuel_records, columns=[
    "date", "petrol_delhi_inr", "diesel_delhi_inr", "source_note"
])

df = spark.createDataFrame(df_pd)
df.write.format("delta").mode("overwrite").saveAsTable("bronze_fuel_prices")
print(f"Fuel prices saved — {df.count()} months")
display(df)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
