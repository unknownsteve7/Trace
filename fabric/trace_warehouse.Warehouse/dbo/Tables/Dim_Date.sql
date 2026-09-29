CREATE TABLE [dbo].[Dim_Date] (
    [date_key]          INT          NOT NULL,
    [date]              DATE         NULL,
    [year]              INT          NULL,
    [quarter]           INT          NULL,
    [month]             INT          NULL,
    [month_name]        VARCHAR (20) NULL,
    [week_of_year]      INT          NULL,
    [day_of_month]      INT          NULL,
    [day_of_week]       INT          NULL,
    [day_name]          VARCHAR (20) NULL,
    [is_weekend]        INT          NULL,
    [is_public_holiday] INT          NULL
);


GO