-- Auto Generated (Do not modify) 9B585F90B2E7032D7A7D4B495DC8D7BC8D2F530C2FC75847DB10F83D95FBCFEE
CREATE   VIEW dbo.vw_route_schedule_summary AS
SELECT
    r.route_id,
    COALESCE(r.route_short_name, r.route_long_name)  AS route_name,
    COUNT(DISTINCT t.trip_id)                         AS total_trips,
    COUNT(s.trip_id)                                  AS total_stop_events,
    SUM(s.is_peak_hour)                               AS peak_hour_stops,
    SUM(CASE WHEN s.is_peak_hour = 0 THEN 1 ELSE 0 END) AS offpeak_stops,
    ROUND(CAST(
        100.0 * SUM(s.is_peak_hour) / NULLIF(COUNT(s.trip_id), 0)
    AS DECIMAL(5,1)), 1)                              AS peak_hour_pct,
    COUNT(DISTINCT s.stop_id)                         AS unique_stops_served
FROM dbo.Fact_TripSchedule   s
JOIN dbo.Dim_Trip             t ON s.trip_id  = t.trip_id
JOIN dbo.Dim_Route            r ON t.route_id = r.route_id
GROUP BY r.route_id, 
         COALESCE(r.route_short_name, r.route_long_name);