CREATE TABLE [dbo].[HourlyTripDistribution] (

	[hour_of_day] int NULL, 
	[total_departures] int NULL, 
	[unique_trips] int NULL, 
	[is_peak_hour] int NULL, 
	[time_slot] varchar(13) NOT NULL
);