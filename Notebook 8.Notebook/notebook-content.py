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
from pyspark.sql.functions import col, to_timestamp, current_timestamp

# URL for the MCTC API CSV Export
# Note: Update this to match your permanent ngrok domain or Render.com URL
MCTC_API_URL = "https://hamstring-reassign-evidence.ngrok-free.dev/export/observations-csv"

print(f"Fetching ground-level observations from: {MCTC_API_URL}")

try:
    # 1. Fetch data directly via pandas
    pdf = pd.read_csv(MCTC_API_URL)
    print(f"Successfully retrieved {len(pdf)} records.")
    
    # 2. Convert to Spark DataFrame
    df = spark.createDataFrame(pdf)
    
    # 3. Clean up data types (convert string timestamps to proper timestamp objects)
    df = df.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
    df = df.withColumn("ingested_at", current_timestamp())
    
    # 4. Save to Bronze Layer in OneLake
    table_name = "bronze_mctc_observations"
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name)
    
    print(f"✅ Data successfully written to {table_name}")

except Exception as e:
    print(f"❌ Error fetching or saving MCTC observations: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
