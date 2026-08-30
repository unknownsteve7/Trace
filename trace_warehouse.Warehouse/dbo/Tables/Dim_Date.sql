CREATE TABLE [dbo].[Dim_Date] (

	[date_key] int NOT NULL, 
	[date] date NULL, 
	[year] int NULL, 
	[quarter] int NULL, 
	[month] int NULL, 
	[month_name] varchar(20) NULL, 
	[week_of_year] int NULL, 
	[day_of_month] int NULL, 
	[day_of_week] int NULL, 
	[day_name] varchar(20) NULL, 
	[is_weekend] int NULL, 
	[is_public_holiday] int NULL
);