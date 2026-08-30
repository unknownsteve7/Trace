CREATE TABLE [dbo].[Fact_VehiclePositions] (

	[entity_id] varchar(50) NULL, 
	[vehicle_id] varchar(50) NULL, 
	[trip_id] varchar(100) NULL, 
	[route_id] varchar(50) NULL, 
	[latitude] float NULL, 
	[longitude] float NULL, 
	[speed] float NULL, 
	[timestamp] varchar(40) NULL, 
	[status] int NULL, 
	[ingested_at] varchar(40) NULL
);