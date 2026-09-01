CREATE TABLE [dbo].[VehicleActivity_Gold] (

	[route_id] varchar(50) NULL, 
	[route_name] varchar(255) NULL, 
	[activity_hour] int NULL, 
	[position_pings] int NULL, 
	[unique_vehicles] int NULL, 
	[avg_speed_kmh] float NULL, 
	[stopped_pings] int NULL, 
	[pct_stopped] numeric(26,12) NULL
);