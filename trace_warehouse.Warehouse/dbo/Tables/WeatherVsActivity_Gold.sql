CREATE TABLE [dbo].[WeatherVsActivity_Gold] (

	[date] date NULL, 
	[weather_label] varchar(50) NULL, 
	[is_rainy_day] int NULL, 
	[precipitation_mm] float NULL, 
	[temp_avg_c] float NULL, 
	[total_pings] int NULL, 
	[active_buses] int NULL, 
	[avg_speed_kmh] float NULL, 
	[stopped_pings] int NULL, 
	[pct_stopped] numeric(26,12) NULL
);