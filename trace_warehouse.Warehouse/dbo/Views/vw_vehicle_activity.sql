-- Auto Generated (Do not modify) 8D667F0A0B4EDA22193B06D7AF704ABDE291148A64A4160CAA621EAEFA902CB3
CREATE   VIEW dbo.vw_vehicle_activity AS
SELECT
    v.route_id,
    COALESCE(r.route_short_name, r.route_long_name) AS route_name,
    CAST(SUBSTRING(v.timestamp, 12, 2) AS INT)      AS activity_hour,
    COUNT(*)                                         AS position_pings,
    COUNT(DISTINCT v.vehicle_id)                     AS unique_vehicles,
    ROUND(AVG(v.speed), 2)                           AS avg_speed_kmh,
    SUM(CASE WHEN v.speed = 0 THEN 1 ELSE 0 END)     AS stopped_pings,
    ROUND(
        100.0 * SUM(CASE WHEN v.speed = 0 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    )                                                AS pct_stopped
FROM dbo.Fact_VehiclePositions v
LEFT JOIN dbo.Dim_Route        r ON v.route_id = r.route_id
GROUP BY v.route_id, 
         COALESCE(r.route_short_name, r.route_long_name),
         CAST(SUBSTRING(v.timestamp, 12, 2) AS INT);