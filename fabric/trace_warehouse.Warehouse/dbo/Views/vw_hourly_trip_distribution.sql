CREATE VIEW dbo.vw_hourly_trip_distribution AS
SELECT
    departure_hour                          AS hour_of_day,
    COUNT(*)                                AS total_departures,
    COUNT(DISTINCT trip_id)                 AS unique_trips,
    SUM(is_peak_hour)                       AS is_peak_hour,
    CASE
        WHEN departure_hour BETWEEN 7  AND 9  THEN 'Morning Peak'
        WHEN departure_hour BETWEEN 17 AND 19 THEN 'Evening Peak'
        WHEN departure_hour BETWEEN 10 AND 16 THEN 'Mid-day'
        WHEN departure_hour BETWEEN 20 AND 23 THEN 'Night'
        ELSE 'Early Morning'
    END                                     AS time_slot
FROM dbo.Fact_TripSchedule
GROUP BY departure_hour
;

GO