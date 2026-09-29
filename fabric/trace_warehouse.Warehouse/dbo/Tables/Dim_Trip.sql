CREATE TABLE [dbo].[Dim_Trip] (
    [trip_id]    VARCHAR (100) NOT NULL,
    [route_id]   VARCHAR (50)  NULL,
    [service_id] VARCHAR (50)  NULL,
    [shape_id]   VARCHAR (50)  NULL,
    [monday]     INT           NULL,
    [tuesday]    INT           NULL,
    [wednesday]  INT           NULL,
    [thursday]   INT           NULL,
    [friday]     INT           NULL,
    [saturday]   INT           NULL,
    [sunday]     INT           NULL,
    [start_date] VARCHAR (20)  NULL,
    [end_date]   VARCHAR (20)  NULL
);


GO