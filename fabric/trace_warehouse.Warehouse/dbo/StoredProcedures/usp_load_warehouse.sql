-- Full reload of the batch (non-realtime) star schema from the lakehouse
-- Silver tables. Run manually after NB01 -> NB07:
--     EXEC dbo.usp_load_warehouse;
CREATE PROCEDURE [dbo].[usp_load_warehouse]
AS
BEGIN
    TRUNCATE TABLE dbo.Dim_Route;
    INSERT INTO dbo.Dim_Route (route_id, route_short_name, route_long_name, route_type)
    SELECT route_id, route_short_name, route_long_name, route_type
    FROM [trace_lakehouse].[dbo].[silver_dim_route];

    TRUNCATE TABLE dbo.Dim_Stop;
    INSERT INTO dbo.Dim_Stop (stop_id, stop_name, stop_lat, stop_lon)
    SELECT stop_id, stop_name, stop_lat, stop_lon
    FROM [trace_lakehouse].[dbo].[silver_dim_stop];

    TRUNCATE TABLE dbo.Dim_Trip;
    INSERT INTO dbo.Dim_Trip
        (trip_id, route_id, service_id, shape_id, monday, tuesday, wednesday,
         thursday, friday, saturday, sunday, start_date, end_date)
    SELECT trip_id, route_id, service_id, shape_id, monday, tuesday, wednesday,
           thursday, friday, saturday, sunday, start_date, end_date
    FROM [trace_lakehouse].[dbo].[silver_dim_trip];

    TRUNCATE TABLE dbo.Dim_Date;
    INSERT INTO dbo.Dim_Date
        (date_key, [date], [year], [quarter], [month], month_name, week_of_year,
         day_of_month, day_of_week, day_name, is_weekend, is_public_holiday)
    SELECT date_key, [date], [year], [quarter], [month], month_name, week_of_year,
           day_of_month, day_of_week, day_name, is_weekend, is_public_holiday
    FROM [trace_lakehouse].[dbo].[silver_dim_date];

    TRUNCATE TABLE dbo.Fact_TripSchedule;
    INSERT INTO dbo.Fact_TripSchedule
        (trip_id, stop_id, stop_sequence, arrival_time, departure_time,
         arrival_secs, departure_secs, departure_hour, is_peak_hour)
    SELECT trip_id, stop_id, stop_sequence, arrival_time, departure_time,
           arrival_secs, departure_secs, departure_hour, is_peak_hour
    FROM [trace_lakehouse].[dbo].[silver_fact_schedule];

    TRUNCATE TABLE dbo.Fact_WeatherDaily;
    INSERT INTO dbo.Fact_WeatherDaily
        ([date], temp_max_c, temp_min_c, temp_avg_c, precipitation_mm,
         windspeed_max_kmh, weather_code, weather_label, is_rainy_day)
    SELECT TRY_CAST([date] AS DATE), temp_max_c, temp_min_c, temp_avg_c, precipitation_mm,
           windspeed_max_kmh, weather_code, weather_label, is_rainy_day
    FROM [trace_lakehouse].[dbo].[silver_fact_weather];

    TRUNCATE TABLE dbo.Fact_FuelPrices;
    INSERT INTO dbo.Fact_FuelPrices ([date], petrol_delhi_inr, diesel_delhi_inr, source_note)
    SELECT TRY_CAST([date] AS DATE), petrol_delhi_inr, diesel_delhi_inr, source_note
    FROM [trace_lakehouse].[dbo].[bronze_fuel_prices];
END


GO
