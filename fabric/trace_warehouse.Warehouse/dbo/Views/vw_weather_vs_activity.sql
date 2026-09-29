CREATE   VIEW dbo.vw_weather_vs_activity AS
SELECT
    w.date,
    w.weather_label,
    w.is_rainy_day,
    w.precipitation_mm,
    w.temp_avg_c,
    COUNT(v.vehicle_id)                                       AS total_pings,
    COUNT(DISTINCT v.vehicle_id)                              AS active_buses,
    ROUND(AVG(v.derived_speed_kmh), 2)                        AS avg_speed_kmh,
    SUM(CASE WHEN v.derived_speed_kmh < 2 THEN 1 ELSE 0 END) AS stopped_pings,
    ROUND(
        100.0 * SUM(CASE WHEN v.derived_speed_kmh < 2 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    )                                                         AS pct_stopped
FROM dbo.Fact_WeatherDaily w
LEFT JOIN dbo.Fact_VehiclePositions v
    ON CAST(SUBSTRING(v.timestamp, 1, 10) AS DATE) = w.date
GROUP BY w.date, w.weather_label, w.is_rainy_day, w.precipitation_mm, w.temp_avg_c;

GO