-- Auto Generated (Do not modify) B7478072A79491BCEFF488C627C56321DECBE5BAD805A554AAD9954A6C73E16E
CREATE VIEW dbo.VehicleActivity_Gold AS
SELECT
    v.route_id,
    r.route_long_name                                              AS route_name,
    CAST(SUBSTRING(v.timestamp, 12, 2) AS INT)                     AS activity_hour,
    CAST(SUBSTRING(v.timestamp, 1, 10) AS DATE)                    AS activity_date,
    COUNT(*)                                                       AS position_pings,
    COUNT(DISTINCT v.vehicle_id)                                   AS unique_vehicles,
    -- Cap at 120 km/h (max realistic Delhi bus speed)
    ROUND(AVG(CASE WHEN v.derived_speed_kmh > 2 
                    AND v.derived_speed_kmh <= 120
                   THEN v.derived_speed_kmh END), 2)               AS avg_speed_kmh,
    SUM(CASE WHEN v.derived_speed_kmh < 2 THEN 1 ELSE 0 END)      AS stopped_pings,
    ROUND(100.0 * SUM(CASE WHEN v.derived_speed_kmh < 2 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1)                                  AS pct_stopped
FROM dbo.Fact_VehiclePositions v
LEFT JOIN dbo.Dim_Route r ON v.route_id = r.route_id
WHERE CAST(SUBSTRING(v.timestamp, 1, 10) AS DATE) >= '2026-09-17'
GROUP BY v.route_id, r.route_long_name,
         CAST(SUBSTRING(v.timestamp, 12, 2) AS INT),
         CAST(SUBSTRING(v.timestamp, 1, 10) AS DATE);