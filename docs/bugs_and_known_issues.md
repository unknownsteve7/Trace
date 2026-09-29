# TRACE — Known Bugs & Issues

> This file tracks known bugs identified during the project audit (Sep 2026).
> Bugs are grouped by severity. Fix these before building the prediction model.

---

## 🔴 HIGH — Will corrupt the prediction model

### BUG-001: GPS Speed Calculation Produces Impossibly High Values
- **File:** `Notebook 2.Notebook/notebook-content.py`
- **Symptom:** `derived_speed_kmh` values up to **44,896 km/h** observed in production (9/29/2026 run)
- **Root Cause:** GPS "glitch" pings (e.g., vehicle_id reuse, `(0,0)` coordinate fallback, cell-tower drift) cause the haversine distance between consecutive pings to be enormous. When divided by a small time delta, speed becomes unrealistically large.
- **Impact:** Any ML model trained on this data will learn that buses can teleport, making delay predictions meaningless.
- **Proposed Fix:** After calculating `derived_speed_kmh`, add a sanity clamp:
  ```python
  .withColumn("derived_speed_kmh",
      when(col("derived_speed_kmh") > 120, None)  # NULL out GPS glitches
      .otherwise(col("derived_speed_kmh"))
  )
  ```
  Also filter out `latitude == 0.0` or `longitude == 0.0` as invalid coordinates before the lag window.
- **Status:** ⏳ Not yet fixed

---

## 🟡 MEDIUM — Data Quality Issues

### BUG-002: Timestamp Timezone Stripping May Cause Incorrect Time Diffs
- **File:** `Notebook 2.Notebook/notebook-content.py`
- **Symptom:** The `regexp_replace` strips `+05:30` from timestamps before computing `unix_timestamp()`. If PySpark's `unix_timestamp()` assumes UTC internally, the absolute time is correct, but the IST-relative display in reports is off by 5.5 hours.
- **Impact:** Peak-hour analysis could misclassify 7:30 AM rush as 2:00 AM.
- **Proposed Fix:** Use `to_utc_timestamp(col("ts_clean"), "Asia/Kolkata")` explicitly.
- **Status:** ⏳ Not yet fixed

### BUG-003: Emoji Characters in Print Statements Cause cp1252 Encoding Errors on Windows
- **File:** `mctc/start_with_tunnel.py` (fixed), other notebooks may still have `✅`/`❌` in comments
- **Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character` when running on Windows CMD
- **Impact:** Pipeline scripts fail to run on Windows terminals without UTF-8 mode
- **Proposed Fix:** Remove emoji from `print()` statements. Already fixed in `start_with_tunnel.py`.
- **Status:** ✅ Partially fixed (start_with_tunnel.py), remaining notebooks not audited

---

## 🟢 LOW — Structural / Technical Debt

### BUG-004: Duplicate Data Pipeline
- **Items:** `Pipeline_Realtime_Ingestion` + `pipeline_realtime_vehicle_positions`
- **Symptom:** Two pipelines both appear to target Notebook 2 (realtime positions). If both run simultaneously they will double-write `bronze_vehicle_positions`, leading to duplicate rows.
- **Status:** ✅ Fixed — `pipeline_realtime_vehicle_positions` removed in Sep 2026 audit

### BUG-005: API Key Exposed in .env.example
- **File:** `.env.example`
- **Symptom:** Real `OTD_API_KEY` committed to public GitHub repo
- **Impact:** Anyone can use the Delhi OTD quota for free
- **Status:** ✅ Fixed — key replaced with placeholder. **ACTION REQUIRED: Rotate the key on the Delhi OTD portal.**

### BUG-006: cloudflared.exe (52MB Binary) Committed to Git
- **File:** `mctc/cloudflared.exe`
- **Status:** ✅ Fixed — removed from git tracking in Sep 2026 audit. Added to `.gitignore`.

---

## Future Work (Stretch Goals)
- [ ] Delay prediction model (requires BUG-001 fix first)
- [ ] RLS for Depot Manager: Replace placeholder `[route_short_name] = "502"` with dynamic `USERPRINCIPALNAME()` lookup
- [ ] Automated MCTC → Lakehouse ingestion (currently manual via NB08)
