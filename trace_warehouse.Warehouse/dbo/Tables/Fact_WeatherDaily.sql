CREATE TABLE [dbo].[Fact_WeatherDaily] (

	[date] date NULL, 
	[temp_max_c] float NULL, 
	[temp_min_c] float NULL, 
	[temp_avg_c] float NULL, 
	[precipitation_mm] float NULL, 
	[windspeed_max_kmh] float NULL, 
	[weather_code] int NULL, 
	[weather_label] varchar(50) NULL, 
	[is_rainy_day] int NULL
);