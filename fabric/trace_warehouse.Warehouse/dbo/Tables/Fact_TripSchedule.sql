CREATE TABLE [dbo].[Fact_TripSchedule] (
    [trip_id]        VARCHAR (100) NULL,
    [stop_id]        VARCHAR (50)  NULL,
    [stop_sequence]  INT           NULL,
    [arrival_time]   VARCHAR (10)  NULL,
    [departure_time] VARCHAR (10)  NULL,
    [arrival_secs]   INT           NULL,
    [departure_secs] INT           NULL,
    [departure_hour] INT           NULL,
    [is_peak_hour]   INT           NULL
);


GO