-- Auto Generated (Do not modify) A9DD5FD38412B983924F97AD06356181B1288071D60A5D5DF116009B2B0F04E5
CREATE VIEW dbo.vw_weather_summary AS
SELECT
    weather_label,
    COUNT(*)                            AS total_days,
    ROUND(AVG(temp_avg_c), 1)           AS avg_temp_c,
    ROUND(AVG(precipitation_mm), 2)     AS avg_rain_mm,
    ROUND(MAX(precipitation_mm), 2)     AS max_rain_mm,
    ROUND(AVG(windspeed_max_kmh), 1)    AS avg_wind_kmh,
    SUM(is_rainy_day)                   AS rainy_days
FROM dbo.Fact_WeatherDaily
GROUP BY weather_label
;