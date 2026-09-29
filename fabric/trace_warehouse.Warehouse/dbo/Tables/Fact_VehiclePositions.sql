CREATE TABLE [dbo].[Fact_VehiclePositions] (
    [entity_id]         VARCHAR (50)  NULL,
    [vehicle_id]        VARCHAR (50)  NULL,
    [trip_id]           VARCHAR (100) NULL,
    [route_id]          VARCHAR (50)  NULL,
    [latitude]          FLOAT (53)    NULL,
    [longitude]         FLOAT (53)    NULL,
    [speed]             FLOAT (53)    NULL,
    [timestamp]         VARCHAR (40)  NULL,
    [status]            INT           NULL,
    [ingested_at]       VARCHAR (40)  NULL,
    [derived_speed_kmh] FLOAT (53)    NULL
);


GO