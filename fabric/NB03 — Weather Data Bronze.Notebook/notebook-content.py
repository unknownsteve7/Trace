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

import requests
import pandas as pd
from pyspark.sql.functions import col

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "start_date": "2026-01-01",
    "end_date": "2026-08-28",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
    "timezone": "Asia/Kolkata"
}

data = requests.get(url, params=params).json()["daily"]
df_pd = pd.DataFrame(data)
df_pd.rename(columns={"time": "date"}, inplace=True)

df = spark.createDataFrame(df_pd)
df.write.format("delta").mode("overwrite").saveAsTable("bronze_weather_daily")
print(f"Weather saved — {df.count()} days")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
