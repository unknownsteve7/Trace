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

import io
import requests
import pandas as pd
from delta.tables import DeltaTable
from pyspark.sql.functions import col, to_timestamp, current_timestamp

# MCTC export endpoint (static ngrok domain — see mctc/start_with_tunnel.py)
MCTC_BASE_URL   = "https://hamstring-reassign-evidence.ngrok-free.dev"
KEY_VAULT_URL   = "https://trace-kv.vault.azure.net/"   # <-- set to your vault
ADMIN_USER      = "admin"
ADMIN_PW_SECRET = "mctc-admin-password"
LOOKBACK_DAYS   = 36500   # pull full history; MERGE below makes re-runs idempotent

TABLE_NAME = "bronze_mctc_observations"

admin_pw = notebookutils.credentials.getSecret(KEY_VAULT_URL, ADMIN_PW_SECRET)
url = f"{MCTC_BASE_URL}/export/observations-csv"
print(f"Fetching ground-level observations from: {url}")

# Errors propagate so a failed fetch fails the notebook run instead of
# reporting success with no data.
resp = requests.get(url, params={"days": LOOKBACK_DAYS},
                    auth=(ADMIN_USER, admin_pw), timeout=60)
resp.raise_for_status()

# All columns as strings (empty -> ""), typed explicitly below
pdf = pd.read_csv(io.StringIO(resp.text), dtype=str, keep_default_na=False)
print(f"Retrieved {len(pdf)} records.")

if pdf.empty:
    print("No observations to ingest.")
else:
    df = (spark.createDataFrame(pdf)
          .withColumn("id", col("id").cast("int"))
          .withColumn("latitude", col("latitude").cast("double"))
          .withColumn("longitude", col("longitude").cast("double"))
          .withColumn("observed_at", to_timestamp(col("observed_at")))
          .withColumn("created_at", to_timestamp(col("created_at")))
          .withColumn("ingested_at", current_timestamp()))

    if spark.catalog.tableExists(TABLE_NAME):
        # Upsert on observation id — status changes (NEW -> REVIEWED) update in place
        (DeltaTable.forName(spark, TABLE_NAME).alias("t")
            .merge(df.alias("s"), "t.id = s.id")
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute())
    else:
        df.write.format("delta").saveAsTable(TABLE_NAME)

    print(f"{TABLE_NAME} now has {spark.table(TABLE_NAME).count()} rows")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
