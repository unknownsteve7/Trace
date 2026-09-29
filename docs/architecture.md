# TRACE — Architecture Overview

## Data Flow

```
[Delhi OTD API]         [Open-Meteo API]      [MCTC Field App]
      |                        |                      |
      v                        v                      v
  NB02 (Realtime)         NB03 (Weather)        NB08 (MCTC Bridge)
      |                        |                      |
      +--------+---------------+----------------------+
               |
          trace_lakehouse (OneLake — Bronze Delta Tables)
               |
               v
  NB05 (Dimensions) + NB06 (TripSchedule Fact)
               |
          Silver Layer (Dim_Route, Dim_Stop, Dim_Trip, Dim_Date, Fact_TripSchedule)
               |
               v
  NB07 (Gold Views & Warehouse Load)
               |
  trace_warehouse (Fabric Warehouse — Star Schema + 6 Gold Views)
               |
               v
  Trace_model.SemanticModel (DirectQuery — Row-Level Security)
               |
               v
  Dashboards.Report (5 Power BI stakeholder dashboards)
```

## Fabric Items

| Item | Type | Purpose |
|---|---|---|
| `trace_lakehouse` | Lakehouse | Bronze + Silver Delta tables |
| `trace_warehouse` | Warehouse | Gold layer star schema & views |
| `Trace_model` | Semantic Model | DirectQuery, RLS for 5 roles |
| `Dashboards` | Power BI Report | 5-page stakeholder dashboards |
| `trace_env` | Environment | PySpark packages (gtfs-rt-bindings, etc.) |
| `Pipeline_Realtime_Ingestion` | Data Pipeline | Schedules NB02 every 5 min |

## Medallion Architecture

| Layer | Tables | Notebooks |
|---|---|---|
| Bronze | `bronze_routes`, `bronze_stops`, `bronze_trips`, `bronze_stop_times`, `bronze_calendar`, `bronze_agency`, `bronze_vehicle_positions`, `Fact_WeatherDaily`, `Fact_FuelPrices`, `bronze_mctc_observations` | NB01–NB04, NB08 |
| Silver | `Dim_Route`, `Dim_Stop`, `Dim_Trip`, `Dim_Date`, `Fact_TripSchedule` | NB05–NB06 |
| Gold | 6 analytical views in `trace_warehouse` | NB07 |

## Row-Level Security Roles

| Role | Restriction |
|---|---|
| Head of Operations Analytics | Full access — no row filter |
| Route Planning Manager | Full access — no row filter |
| Depot Manager | Filtered to assigned depot routes via `Dim_Route` |
| Fleet & Maintenance Manager | Full access — no row filter |
| Customer Experience Head | Full access — no row filter |
