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

bronze_wx = spark.table("bronze_weather_daily")
bronze_wx.printSchema()
display(bronze_wx.limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col, when, round as spark_round

def wmo_label(code_col):
    return (
        when(code_col == 0,  "Clear sky")
        .when(code_col.between(1, 3),   "Partly cloudy")
        .when(code_col.between(45, 48), "Foggy")
        .when(code_col.between(51, 67), "Drizzle/Rain")
        .when(code_col.between(71, 77), "Snow")
        .when(code_col.between(80, 82), "Rain showers")
        .when(code_col.between(95, 99), "Thunderstorm")
        .otherwise("Other")
    )

silver_weather = bronze_wx.select(
    col("date"),
    spark_round(col("temperature_2m_max").cast("double"), 1).alias("temp_max_c"),
    spark_round(col("temperature_2m_min").cast("double"), 1).alias("temp_min_c"),
    spark_round(
        (col("temperature_2m_max").cast("double") + col("temperature_2m_min").cast("double")) / 2,
        1
    ).alias("temp_avg_c"),
    spark_round(col("precipitation_sum").cast("double"), 2).alias("precipitation_mm"),
    spark_round(col("windspeed_10m_max").cast("double"), 1).alias("windspeed_max_kmh"),
    col("weathercode").cast("int").alias("weather_code"),
    wmo_label(col("weathercode").cast("int")).alias("weather_label"),
    when(col("precipitation_sum").cast("double") > 1.0, 1).otherwise(0).alias("is_rainy_day")
)

silver_weather.write.format("delta").mode("overwrite").saveAsTable("silver_fact_weather")
print(f"Silver Weather — {silver_weather.count()} days")
display(silver_weather.limit(10))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

spark.sql("""
    SELECT
        weather_label,
        COUNT(*) as days,
        ROUND(AVG(temp_avg_c), 1) as avg_temp,
        ROUND(AVG(precipitation_mm), 2) as avg_rain_mm
    FROM silver_fact_weather
    GROUP BY weather_label
    ORDER BY days DESC
""").show()


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
