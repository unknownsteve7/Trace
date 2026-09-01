CREATE TABLE [dbo].[RouteScheduleSummary_Gold] (

	[route_id] varchar(50) NOT NULL, 
	[route_name] varchar(255) NULL, 
	[total_trips] int NULL, 
	[total_stop_events] int NULL, 
	[peak_hour_stops] int NULL, 
	[offpeak_stops] int NULL, 
	[peak_hour_pct] decimal(5,1) NULL, 
	[unique_stops_served] int NULL
);