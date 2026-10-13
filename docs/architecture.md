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
  NB07 (Weather Silver) + NB09 (Data Quality Checks)
               |
  usp_load_warehouse / usp_load_vehicle_positions (cross-database INSERT)
               |
  trace_warehouse (Fabric Warehouse — Star Schema + 6 Gold Views)
               |
               v
  Trace_model.SemanticModel (Direct Lake — Row-Level Security)
               |
               v
  Dashboards.Report (5 Power BI stakeholder dashboards)
```

## Fabric Items

| Item | Type | Purpose |
|---|---|---|
| `trace_lakehouse` | Lakehouse | Bronze + Silver Delta tables |
| `trace_warehouse` | Warehouse | Gold layer star schema & views |
| `Trace_model` | Semantic Model | Direct Lake, RLS for 5 roles |
| `Dashboards` | Power BI Report | 5-page stakeholder dashboards |
| `trace_env` | Environment | PySpark packages (gtfs-rt-bindings, etc.) |
| `Pipeline_Realtime_Ingestion` | Data Pipeline | Every 10 min: NB02, then `usp_load_vehicle_positions` |

## Medallion Architecture

| Layer | Tables | Notebooks |
|---|---|---|
| Bronze | `bronze_routes`, `bronze_stops`, `bronze_trips`, `bronze_stop_times`, `bronze_calendar`, `bronze_agency`, `bronze_vehicle_positions`, `Fact_WeatherDaily`, `Fact_FuelPrices`, `bronze_mctc_observations` | NB01–NB04, NB08 |
| Silver | `silver_dim_route`, `silver_dim_stop`, `silver_dim_trip`, `silver_dim_date`, `silver_fact_schedule`, `silver_fact_weather`, `silver_vehicle_positions` | NB02, NB05–NB07 |
| Gold | Star schema + 6 `*_Gold` views in `trace_warehouse` | Stored procedures `usp_load_warehouse`, `usp_load_vehicle_positions` |

## Row-Level Security Roles

| Role | Restriction |
|---|---|
| Head of Operations Analytics | Full access — no row filter |
| Route Planning Manager | Full access — no row filter |
| Depot Manager | Dynamic: `Dim_Route` filtered to routes mapped to `USERPRINCIPALNAME()` in `UserRouteAccess` |
| Fleet & Maintenance Manager | Full access — no row filter |
| Customer Experience Head | Full access — no row filter |

## Secrets

No credentials are stored in the repo. Fabric notebooks read them from Azure Key Vault via `notebookutils.credentials.getSecret`:

| Secret | Used by |
|---|---|
| `otd-api-key` | NB02 — Delhi OTD realtime API |
| `mctc-admin-password` | NB08 — MCTC CSV export (HTTP Basic) |

The MCTC app reads `ADMIN_PASSWORD` and `NGROK_AUTH_TOKEN` from `mctc/.env` (see `mctc/.env.example`).
