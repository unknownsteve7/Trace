# TRACE
### Transit Analytics & Reliability Correlation Engine

An end-to-end data engineering pipeline and analytics platform for **Delhi's DTC bus network**, built on real government transit data. TRACE ingests schedule, live vehicle position, weather, and fuel-price data to surface delay patterns, reliability trends, and operational insights — from raw public data to a Power BI dashboard.

---

##  Overview

Public transit agencies generate enormous amounts of operational data, but that data is rarely connected to the external factors that actually drive service reliability — weather, fuel costs, route load. TRACE builds a complete analytics pipeline around Delhi's official [Open Transit Data (OTD)](https://otd.delhi.gov.in/) portal to answer questions like:

- Which routes and time slots have the worst on-time performance?
- How does weather correlate with delays?
- Where are complaint hotspots, and do they align with actual performance data?
- How do fuel price trends track against operational patterns?

The project is intentionally built on **real, verifiable, government-published data sources** rather than synthetic or fictional data, so every analytical claim is traceable back to its origin.

---

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources   │───▶│   ETL Pipeline    │───▶│   PostgreSQL     │
│                  │    │   (Python)        │    │  (Star Schema)   │
│ • Delhi OTD GTFS │    │                   │    └────────┬─────────┘
│ • OTD Realtime   │    │  Extract          │             │
│ • Open-Meteo     │    │  Transform        │             ▼
│ • PPAC (scraped) │    │  Load             │    ┌─────────────────┐
│ • data.gov.in    │    └──────────────────┘    │   Power BI       │
└─────────────────┘                              │  (RLS-secured)   │
        ▲                                        └─────────────────┘
        │
┌─────────────────┐
│  QR Complaint    │
│  System (FastAPI)│──────────────────▶ Fact_Complaints
└─────────────────┘
```

---

##  Data Sources

| Source | What it provides | Access |
|---|---|---|
| [Delhi OTD](https://otd.delhi.gov.in/) — Static GTFS | DTC bus stops, routes, trips, schedules | ZIP download (3,464 stops · 543 routes · 16,562 trips) |
| Delhi OTD — Realtime GTFS | Live vehicle positions (Protocol Buffers) | Authenticated API |
| [Open-Meteo](https://open-meteo.com/) | Historical weather for Delhi | Free REST API |
| PPAC | Daily petrol/diesel prices | Web scraping |
| [data.gov.in](https://data.gov.in/) | Supplementary transport datasets | REST API |

> **Scope note:** Delhi Metro (DMRC) data is intentionally excluded. It's a different transport mode with different operational dynamics — including it would dilute the project's focus without adding proportional analytical value.

---

## Data Model

Star schema design:

**Fact tables**
- `Fact_TripSchedule` — scheduled stop-times (grain: one row per scheduled stop event)
- `Fact_TripActual` — actual vehicle positions/updates from the realtime feed
- `Fact_Complaints` — rider-submitted complaints via QR system
- `Fact_WeatherDaily` — daily weather observations

**Dimension tables**
- `Dim_Route` · `Dim_Stop` · `Dim_Trip` · `Dim_Date`

---

##  Tech Stack

- **Python** — pandas, requests, BeautifulSoup, gtfs-realtime-bindings
- **FastAPI** — QR complaint capture backend
- **PostgreSQL** — data warehouse
- **Power BI** — dashboards with Row-Level Security
- **Protocol Buffers** — realtime feed decoding

---

##  Project Structure

```
trace/
├── data/
│   ├── raw/                 # Extracted, untouched source data
│   └── processed/           # Cleaned, transformed data
├── src/
│   ├── extract/              # Source-specific fetch scripts
│   ├── transform/            # Cleaning & feature engineering
│   ├── load/                 # PostgreSQL load scripts
│   └── analysis/             # SQL analysis queries
├── complaint_system/
│   ├── main.py                # FastAPI app
│   └── seed_data/             # Seed complaint dataset
├── dashboards/                # Power BI files
├── docs/
│   └── TRACE_Project_Overview.md
└── README.md
```

---

##  Setup

```bash
# Clone the repository
git clone https://github.com/unknownsteve7/trace.git
cd trace

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Add your Delhi OTD realtime API key, data.gov.in API key, and DB credentials
```

---

##  Pipeline Stages

1. **Extract** — pull static GTFS, realtime vehicle positions, weather, and fuel price data
2. **Transform** — parse GTFS time formats, align sources on date keys, engineer features (`is_peak_hour`, `is_weekend`, etc.)
3. **Load** — idempotent load into the PostgreSQL star schema
4. **Analyze** — SQL queries covering on-time performance, weather correlation, headway consistency, and complaint hotspots
5. **Visualize** — Power BI dashboards for Operations, Complaints, and Cost impact

---

## Sample Analytical Questions

- Which routes have the lowest on-time performance during peak hours?
- Is there a statistically meaningful relationship between rainfall and delay duration?
- Which routes generate disproportionately high complaint volume relative to their schedule frequency?
- How do fuel price trends align with reported operational patterns?

---

##  Roadmap

- [x] Finalize scope and real data source (Delhi OTD)
- [x] Obtain realtime API access
- [ ] Complete ETL pipeline
- [ ] Build QR complaint capture system
- [ ] SQL analysis layer
- [ ] Power BI dashboards with RLS
- [ ] (Stretch) Delay prediction model

---

##  Author

**Naga Mohan Madicharla**
B.Tech CSE, RGUKT Ongole
[Portfolio](https://nagamohan.me) · [GitHub](https://github.com/unknownsteve7) · [LinkedIn](https://linkedin.com/in/nagamohan765/)