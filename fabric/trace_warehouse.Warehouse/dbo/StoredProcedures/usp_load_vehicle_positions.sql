-- Loads silver_vehicle_positions (lakehouse) into Fact_VehiclePositions.
-- Called by Pipeline_Realtime_Ingestion after NB02 every run.
-- Incremental by ingested_at (second granularity is safe: batches are
-- minutes apart). Pass @full_reload = 1 once after deploying the BUG-001
-- fix to replace rows that still carry unclamped speeds.
CREATE PROCEDURE [dbo].[usp_load_vehicle_positions]
    @full_reload BIT = 0
AS
BEGIN
    DECLARE @watermark DATETIME2 (0);

    IF @full_reload = 1
        TRUNCATE TABLE dbo.Fact_VehiclePositions;
    ELSE
        SELECT @watermark = MAX(TRY_CAST(LEFT(ingested_at, 19) AS DATETIME2 (0)))
        FROM dbo.Fact_VehiclePositions;

    INSERT INTO dbo.Fact_VehiclePositions
        (entity_id, vehicle_id, trip_id, route_id, latitude, longitude,
         speed, [timestamp], status, ingested_at, derived_speed_kmh)
    SELECT
        entity_id, vehicle_id, trip_id, route_id, latitude, longitude,
        speed, [timestamp], status, ingested_at, derived_speed_kmh
    FROM [trace_lakehouse].[dbo].[silver_vehicle_positions]
    WHERE @watermark IS NULL
       OR TRY_CAST(LEFT(ingested_at, 19) AS DATETIME2 (0)) > @watermark;
END


GO
