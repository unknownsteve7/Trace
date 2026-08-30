-- Auto Generated (Do not modify) 76F3BC73373F62B548674083D0E8410D4BEACCF30A92ED5C3B6E040C9576BE39


CREATE   VIEW dbo.vw_top_routes AS
SELECT TOP 50
    r.route_id,
    COALESCE(r.route_short_name, r.route_long_name) AS route_name,
    COUNT(DISTINCT t.trip_id)                        AS scheduled_trips,
    COUNT(s.stop_id)                                 AS total_stop_events,
    COUNT(DISTINCT s.stop_id)                        AS unique_stops,
    SUM(s.is_peak_hour)                              AS peak_events
FROM dbo.Fact_TripSchedule  s
JOIN dbo.Dim_Trip            t ON s.trip_id  = t.trip_id
JOIN dbo.Dim_Route           r ON t.route_id = r.route_id
GROUP BY r.route_id, 
         COALESCE(r.route_short_name, r.route_long_name)
ORDER BY scheduled_trips DESC;