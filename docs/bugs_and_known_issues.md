# TRACE — Known Bugs & Issues

> This file tracks known bugs identified during the project audits (Sep & Oct 2026).
> Bugs are grouped by severity.

---

## 🔴 HIGH — Will corrupt the prediction model

### BUG-001: GPS Speed Calculation Produces Impossibly High Values
- **File:** `fabric/NB02 — Realtime Positions Bronze.Notebook/notebook-content.py`
- **Symptom:** `derived_speed_kmh` values up to **44,896 km/h** observed in production (9/29/2026 run)
- **Root Cause:** GPS "glitch" pings (e.g., vehicle_id reuse, `(0,0)` coordinate fallback, cell-tower drift) cause the haversine distance between consecutive pings to be enormous. When divided by a small time delta, speed becomes unrealistically large.
- **Impact:** Any ML model trained on this data will learn that buses can teleport, making delay predictions meaningless.
- **Fix:** Derived speed moved to `silver_vehicle_positions`. Pings outside the Delhi NCR bounding box (incl. `(0,0)`) are dropped, duplicate `(vehicle_id, timestamp)` pings removed, and speeds > 120 km/h set to NULL. NB09 asserts no row exceeds 120 km/h.
- **Status:** ✅ Fixed (Oct 2026). Run `EXEC dbo.usp_load_vehicle_positions @full_reload = 1;` once to replace warehouse rows loaded before the fix.

---

## 🟡 MEDIUM — Data Quality Issues

### BUG-002: Timestamp Timezone Stripping May Cause Incorrect Time Diffs
- **File:** `fabric/NB02 — Realtime Positions Bronze.Notebook/notebook-content.py`
- **Symptom:** The `regexp_replace` stripped `+05:30` from timestamps before computing `unix_timestamp()`, making the instant depend on the Spark session time zone.
- **Impact:** Peak-hour analysis could misclassify 7:30 AM rush as 2:00 AM.
- **Fix:** The full ISO string (with offset) is parsed via `to_timestamp`, so the instant is exact regardless of session time zone. The IST string column is kept for hour-of-day in the warehouse views.
- **Status:** ✅ Fixed (Oct 2026)

### BUG-003: Emoji Characters in Print Statements Cause cp1252 Encoding Errors on Windows
- **File:** `mctc/start_with_tunnel.py`
- **Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character` when running on Windows CMD
- **Status:** ✅ Fixed — no emoji remain in `print()` calls in `mctc/` or `fabric/` (audited Oct 2026)

### BUG-007: Bronze Table Rewritten on Every Realtime Run
- **File:** `fabric/NB02 — Realtime Positions Bronze.Notebook/notebook-content.py`
- **Symptom:** Every 10-minute run read all of `bronze_vehicle_positions`, recomputed speeds, and overwrote the table — cost grew with table size, and a failure mid-write risked data loss.
- **Fix:** Bronze is append-only; Silver is built incrementally from rows newer than its `ingested_at` watermark.
- **Status:** ✅ Fixed (Oct 2026)

### BUG-008: MCTC Bridge (NB08) Never Wrote Data
- **File:** `fabric/NB8_Ingest_MCTC_Observations.Notebook/notebook-content.py`
- **Symptom:** NB08 converted a `timestamp` column the CSV export doesn't have; the error was swallowed by `try/except: print`, so runs appeared successful. It also overwrote the table with only the last 7 days.
- **Fix:** Converts `observed_at` / `created_at`, fetches full history, MERGEs on `id`, and lets errors fail the run.
- **Status:** ✅ Fixed (Oct 2026)

### BUG-009: Warehouse Load Not in Source Control / Not Scheduled
- **Symptom:** Nothing in the repo loaded the warehouse from the lakehouse, so new realtime pings never reached the dashboards automatically.
- **Fix:** `dbo.usp_load_warehouse` (full reload of batch tables) and `dbo.usp_load_vehicle_positions` (incremental), the latter run by the pipeline after NB02.
- **Status:** ✅ Fixed (Oct 2026)

---

## 🟢 LOW — Structural / Technical Debt

### BUG-004: Duplicate Data Pipeline
- **Items:** `Pipeline_Realtime_Ingestion` + `pipeline_realtime_vehicle_positions`
- **Status:** ✅ Fixed — `pipeline_realtime_vehicle_positions` removed in Sep 2026 audit

### BUG-005: Secrets Committed to Git
- **Files:** `.env.example` (Sep 2026), `NB02` OTD API key and `mctc/start_with_tunnel.py` ngrok token (found Oct 2026)
- **Impact:** Anyone with repo access (and anyone reading git history) can use these credentials
- **Fix:** Notebooks read secrets from Azure Key Vault; MCTC reads them from `mctc/.env`.
- **Status:** ✅ Removed from code. **ACTION REQUIRED: rotate the OTD API key and the ngrok auth token** — they remain in git history.

### BUG-006: cloudflared.exe (52MB Binary) Committed to Git
- **Status:** ✅ Fixed — removed from git tracking in Sep 2026 audit. Added to `.gitignore`.

### BUG-010: Duplicate Warehouse Views
- **Symptom:** Six `vw_*` views duplicated the six `*_Gold` views with diverging logic (the `vw_*` versions lacked the 120 km/h speed cap).
- **Status:** ✅ Fixed — `vw_*` views removed; the semantic model only uses `*_Gold`.

### BUG-011: Pipeline Schedule Expired
- **Symptom:** `.schedules` ended 2026-10-05, so realtime ingestion silently stopped.
- **Status:** ✅ Fixed — extended to 2026-12-31. Extend again (and Dim_Date, currently to 2027-12-31) as needed.

---

## Future Work (Stretch Goals)
- [ ] Delay prediction model (BUG-001 now fixed)
- [x] RLS for Depot Manager: dynamic `USERPRINCIPALNAME()` lookup via `dbo.UserRouteAccess` (populate the table to grant access)
- [ ] Automated MCTC → Lakehouse ingestion (NB08 still run manually)
