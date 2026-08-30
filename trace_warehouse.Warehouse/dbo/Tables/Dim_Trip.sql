CREATE TABLE [dbo].[Dim_Trip] (

	[trip_id] varchar(100) NOT NULL, 
	[route_id] varchar(50) NULL, 
	[service_id] varchar(50) NULL, 
	[shape_id] varchar(50) NULL, 
	[monday] int NULL, 
	[tuesday] int NULL, 
	[wednesday] int NULL, 
	[thursday] int NULL, 
	[friday] int NULL, 
	[saturday] int NULL, 
	[sunday] int NULL, 
	[start_date] varchar(20) NULL, 
	[end_date] varchar(20) NULL
);