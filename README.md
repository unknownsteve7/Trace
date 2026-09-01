# TRACE
### Transit Analytics & Reliability Correlation Engine

An end-to-end cloud data engineering and analytics platform for **Delhi's DTC bus network**, built on **Microsoft Fabric**. TRACE ingests schedule, live vehicle position, weather, and fuel-price data through a medallion lakehouse architecture to surface delay patterns, reliability trends, and operational insights — from raw government data to interactive Power BI dashboards.

---

## Overview

Public transit agencies generate enormous amounts of operational data, but that data is rarely connected to the external factors that actually drive service reliability — weather, fuel costs, route load. TRACE builds a complete cloud analytics pipeline around Delhi's official [Open Transit Data (OTD)](https://otd.delhi.gov.in/) portal to answer questions like:

- Which routes and time slots have the worst on-time performance?
- How does weather correlate with bus speeds and stoppages?
- What does Delhi's DTC service pattern look like across peak vs. off-peak hours?
- How do fuel price trends track against operational patterns?

The project is built on **real, verifiable, government-published data sources** — every analytical claim is traceable back to its origin.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│  Delhi OTD GTFS (Static)  •  OTD Realtime API  •  Open-Meteo   │
│  PPAC / IOCL Fuel Prices  •  data.gov.in                        │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                  MICROSOFT FABRIC — TRACE Workspace              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Fabric Notebooks (PySpark)                  │    │
│  │  NB1: GTFS Static Extract  │  NB2: Realtime Positions   │    │
│  │  NB3: Weather Extract      │  NB4: Fuel Prices Seed     │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           OneLake — trace_lakehouse (Delta)              │    │
│  │                                                          │    │
│  │  BRONZE (raw)           SILVER (clean)                   │    │
│  │  bronze_routes          silver_dim_route                 │    │
│  │  bronze_stops           silver_dim_stop                  │    │
│  │  bronze_trips           silver_dim_trip                  │    │
│  │  bronze_stop_times      silver_dim_date                  │    │
│  │  bronze_vehicle_pos     silver_fact_schedule             │    │
│  │  bronze_weather_daily   silver_fact_weather              │    │
│  │  bronze_fuel_prices                                      │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                         │  Cross-database SQL INSERT             │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           trace_warehouse (Fabric Warehouse)             │    │
│  │                                                          │    │
│  │  DIMENSION TABLES       FACT TABLES                      │    │
│  │  Dim_Route              Fact_TripSchedule                │    │
│  │  Dim_Stop               Fact_VehiclePositions            │    │
│  │  Dim_Trip               Fact_WeatherDaily                │    │
│  │  Dim_Date               Fact_FuelPrices                  │    │
│  │                                                          │    │
│  │  ANALYSIS VIEWS                                          │    │
│  │  vw_route_schedule_summary                               │    │
│  │  vw_hourly_trip_distribution                             │    │
│  │  vw_vehicle_activity                                     │    │
│  │  vw_weather_summary                                      │    │
│  │  vw_weather_vs_activity                                  │    │
│  │  vw_top_routes                                           │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │     Trace_Model (Semantic Model — DirectQuery)           │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Power BI Reports (in Fabric)                │    │
│  │   Operations Dashboard  •  Weather Dashboard             │    │
│  │   Cost & Fuel Dashboard                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

| Source | What it provides | Access |
|---|---|---|
| [Delhi OTD](https://otd.delhi.gov.in/) — Static GTFS | DTC bus stops, routes, trips, schedules | ZIP download (3,464 stops · 543 routes · 16,562 trips) |
| Delhi OTD — Realtime GTFS | Live vehicle positions (Protocol Buffers) | Authenticated API key |
| [Open-Meteo](https://open-meteo.com/) | Historical daily weather for Delhi | Free REST API |
| IOCL SMS Service | Current petrol/diesel retail prices | SMS `RSP <code>` to 7588888824 |
| Seeded historical prices | Monthly petrol/diesel prices 2024–2026 | PPAC/IOCL verified |

> **Scope note:** Delhi Metro (DMRC) is intentionally excluded — it's a different mode with different operational dynamics.

---

## Data Model

**Medallion Architecture (Bronze → Silver → Gold)**

| Layer | Location | Description |
|---|---|---|
| Bronze | `trace_lakehouse` Delta tables | Raw ingested data, untransformed |
| Silver | `trace_lakehouse` Delta tables | Cleaned, typed, feature-engineered |
| Gold | `trace_warehouse` + Views | Star schema ready for reporting |

**Star Schema**

```
Dim_Route ──┐
Dim_Stop  ──┤
Dim_Trip  ──┼──► Fact_TripSchedule
Dim_Date  ──┤    Fact_VehiclePositions
            │    Fact_WeatherDaily
            └    Fact_FuelPrices
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Cloud Platform | Microsoft Fabric |
| Ingestion & Transform | PySpark (Fabric Notebooks) |
| Storage | OneLake — Delta tables (medallion) |
| Warehouse | Fabric Warehouse (T-SQL) |
| Semantic Layer | Fabric Semantic Model (DirectQuery) |
| Dashboards | Power BI (in Fabric) |
| Realtime decoding | `gtfs-realtime-bindings` (Protocol Buffers) |
| Version Control | Git — synced Azure Repos ↔ GitHub |

---

## Project Structure

```
trace/
├── Notebook 1.Notebook/          # Extract: GTFS static → Bronze Delta tables
├── Notebook 2.Notebook/          # Extract: Realtime vehicle positions → Bronze
├── Notebook 3.Notebook/          # Extract: Open-Meteo weather → Bronze
├── Notebook 4.Notebook/          # Seed: Fuel prices → Bronze
├── Notebook 5.Notebook/          # Transform: Dim_Route/Stop/Trip/Date → Silver
├── Notebook 6.Notebook/          # Transform: Fact_TripSchedule → Silver
├── Notebook 7.Notebook/          # Transform: Fact_WeatherDaily → Silver
├── trace_lakehouse.Lakehouse/    # Lakehouse definition (synced from Fabric)
├── trace_warehouse.Warehouse/    # Warehouse DDL — all table definitions
│   └── dbo/Tables/               # Dim_*.sql · Fact_*.sql
├── Trace_Model.SemanticModel/    # Power BI semantic model definition
│   └── definition/tables/        # One .tmdl per table/view
├── notebook/
│   └── scraping.ipynb            # Local POC — API connectivity tests
├── src/                          # Placeholder for local ETL scripts
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
└── README.md
```

---

## Fabric Concepts Demonstrated

| Concept | Implementation |
|---|---|
| Medallion Architecture | Bronze → Silver → Gold layers in OneLake |
| Delta Tables | All lakehouse tables use Delta format (ACID, versioned) |
| Cross-database Queries | Warehouse pulls from Lakehouse via `[trace_lakehouse].[dbo].[table]` |
| Fabric Notebooks | PySpark for all ETL — extract, transform, load |
| Semantic Model | DirectQuery model over Warehouse views |
| Git Integration | Azure DevOps Git → Fabric workspace sync |

---


### Fabric deployment

1. Connect your Fabric workspace to this Git repository (Azure DevOps or GitHub)
2. Sync — all notebooks, warehouse, lakehouse, and semantic model will import automatically
3. Upload GTFS static files to `trace_lakehouse/Files/` (download from Delhi OTD)
4. Run notebooks in order: **NB1 → NB2 → NB3 → NB4 → NB5 → NB6 → NB7**
5. Run the Warehouse SQL load script to populate Dim/Fact tables from Silver layer
6. Open `Trace_Model` semantic model → build Power BI reports

---

## Dashboard Stakeholders & RLS

| Role | Dashboard Access | Row-Level Security |
|---|---|---|
| Head of Operations Analytics | All dashboards | Unrestricted |
| Route Planning Manager | Operations — Service Pattern, Top Routes | All routes |
| Depot Manager | Operations — Vehicle Activity | Own depot's routes only |
| Fleet & Maintenance Manager | Vehicle Activity, speed/stoppage metrics | All vehicles |
| Customer Experience Head | Weather Impact, Complaints (planned) | All routes |

---

## Sample Analytical Questions

- Which routes carry the most scheduled stop events during morning peak (07:00–09:00)?
- Does rainfall correlate with higher bus stoppages on Delhi roads?
- What is the peak-hour vs. off-peak service split across the DTC network?
- Which routes have the highest unique stop coverage (network reach)?
- How do current fuel prices compare to the baseline over the project period?

---

## Roadmap

- [x] Finalize scope and data sources (Delhi OTD)
- [x] Obtain realtime API access
- [x] GTFS static data extracted → Bronze layer
- [x] Realtime vehicle positions → Bronze layer
- [x] Weather data (Open-Meteo historical) → Bronze layer
- [x] Fuel prices seeded → Bronze layer
- [x] Dimension tables built → Silver layer
- [x] Fact_TripSchedule with peak-hour features → Silver layer
- [x] Star schema created in Fabric Warehouse
- [x] SQL analysis views (6 views covering OTP, weather, activity)
- [x] Semantic model (DirectQuery over Warehouse)
- [ ] Power BI dashboards — Operations, Weather, Cost
- [ ] Row-Level Security by stakeholder role
- [ ] Data Factory pipeline — scheduled Notebook 2 (realtime ingestion)
- [ ] QR complaint capture system (FastAPI)
- [ ] (Stretch) Delay prediction model

---

## Author

**Naga Mohan Madicharla**  
B.Tech CSE, RGUKT Ongole  
[Portfolio](https://nagamohan.me) · [GitHub](https://github.com/unknownsteve7) · [LinkedIn](https://linkedin.com/in/nagamohan765/)
