CREATE TABLE [dbo].[Fact_WeatherDaily] (
    [date]              DATE         NULL,
    [temp_max_c]        FLOAT (53)   NULL,
    [temp_min_c]        FLOAT (53)   NULL,
    [temp_avg_c]        FLOAT (53)   NULL,
    [precipitation_mm]  FLOAT (53)   NULL,
    [windspeed_max_kmh] FLOAT (53)   NULL,
    [weather_code]      INT          NULL,
    [weather_label]     VARCHAR (50) NULL,
    [is_rainy_day]      INT          NULL
);


GO