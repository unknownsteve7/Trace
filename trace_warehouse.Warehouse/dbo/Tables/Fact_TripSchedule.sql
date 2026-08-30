CREATE TABLE [dbo].[Fact_TripSchedule] (

	[trip_id] varchar(100) NULL, 
	[stop_id] varchar(50) NULL, 
	[stop_sequence] int NULL, 
	[arrival_time] varchar(10) NULL, 
	[departure_time] varchar(10) NULL, 
	[arrival_secs] int NULL, 
	[departure_secs] int NULL, 
	[departure_hour] int NULL, 
	[is_peak_hour] int NULL
);