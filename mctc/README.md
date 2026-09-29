# MCTC Ground-Level Operational Observation System (Prototype)

## 0. What this is (and what it is NOT)

This is **not** a passenger complaint app.

It is a small backend service that lets someone physically present near a
bus scan a QR code and record a **ground-level operational observation**
(e.g. "this bus is overcrowded", "this bus has not arrived", "vehicle
condition looks poor").

These observations are **raw evidence**. On their own they don't prove a
system-wide problem. Later, MCTC's analytics layer will combine many such
observations with real operational datasets — GPS, GTFS schedules,
ridership, weather, traffic, fuel and maintenance data — to identify
*actual recurring operational problems* (e.g. "Route R101 has a
structural overcrowding problem during evening peak", not just "one
person said it was crowded once").

```
QR observations + GPS + GTFS + Ridership + Weather + Traffic + Fuel + Maintenance
        │
        ▼
  Operational Analytics (future system)
        │
        ▼
  Identify recurring problems → Administrator decisions
```

This module's job stops at collecting clean, structured, well-categorized
observations. It deliberately does NOT try to diagnose problems itself.

---

## 1. Project structure

```
mctc_qr_feedback/
│
├── main.py            # FastAPI app: all HTTP endpoints/routes
├── database.py         # SQLAlchemy engine, session, Base, get_db dependency
├── models.py           # SQLAlchemy ORM tables (QRCode, Observation) + Enums
├── schemas.py           # Pydantic request/response models
├── crud.py               # Database access functions (create/read/update)
├── requirements.txt       # Python dependencies
├── .env                    # DATABASE_URL (SQLite, local file)
├── .gitignore                # Files excluded from version control
└── README.md                   # This file
```

**File responsibilities, in plain terms:**

- **`database.py`** — creates the SQLite engine/connection, the session
  factory, and the `Base` class all ORM models inherit from. Also
  provides `get_db()`, a FastAPI dependency that opens a DB session per
  request and closes it afterward.
- **`models.py`** — defines the two database tables (`qr_codes`,
  `observations`) as Python classes, plus the three Enums
  (`ProblemType`, `Severity`, `ObservationStatus`) that constrain what
  values are allowed.
- **`schemas.py`** — defines the Pydantic models FastAPI uses to
  validate incoming JSON and to shape outgoing JSON. Kept separate from
  `models.py` so "how it's stored" and "what the API looks like" can
  evolve independently.
- **`crud.py`** — all direct database queries (create QR code, look up
  by token, check for duplicate submission, filter observations,
  compute summary stats). Keeps `main.py` focused on HTTP concerns.
- **`main.py`** — the FastAPI app itself: wires up every endpoint,
  calls into `crud.py`, and returns responses shaped by `schemas.py`.

---

## 2. Database schema

### `qr_codes`

| Column      | Type      | Notes                                  |
|-------------|-----------|-----------------------------------------|
| id          | Integer   | Primary key                             |
| qr_token    | String    | Unique. This is what's encoded in the QR URL |
| bus_number  | String    | Optional                                |
| route_id    | String    | Optional                                |
| location    | String    | Optional, e.g. "Inside bus"             |
| is_active   | Boolean   | Default true                            |
| created_at  | DateTime  | Set automatically on insert             |

Only the token is stored — **no QR image data is stored in the
database**. The actual QR image (if/when generated) would just encode
the URL `http://127.0.0.1:8000/observe/{qr_token}`.

### `observations`

| Column                | Type      | Notes                                              |
|------------------------|-----------|-----------------------------------------------------|
| id                     | Integer   | Primary key                                         |
| qr_code_id             | Integer   | Foreign key → `qr_codes.id`                         |
| bus_number             | String    | Optional; copied from the QR code at submit time    |
| route_id               | String    | Optional; copied from the QR code at submit time    |
| problem_type           | Enum      | One of 16 operational categories (see below)        |
| severity               | Enum      | LOW / MEDIUM / HIGH / CRITICAL                       |
| description            | Text      | Optional, max 1000 characters                       |
| observed_at            | DateTime  | When the problem was actually observed              |
| latitude               | Float     | Optional                                             |
| longitude              | Float     | Optional                                             |
| anonymous_identifier   | String    | Duplicate-submission control only — NOT an identity  |
| status                 | Enum      | NEW / REVIEWED / RESOLVED                            |
| created_at             | DateTime  | When the row was inserted into the database          |

**Relationship:** one `QRCode` → many `Observation` rows, via
`observations.qr_code_id`.

**No unnecessary PII is collected.** No name, phone number, email,
government ID, or password is ever asked for.

**Why `bus_number`/`route_id` are duplicated onto the observation row:**
a QR code's physical bus/route assignment could change later (e.g. the
QR sticker is moved to a different bus). Copying the values at
submission time preserves what was true *at the moment of the
observation*, which matters for later time-based correlation with GPS
and GTFS data.

---

## 3. Enums

### Problem categories (`ProblemType`)

These are **operational** categories meant to be cross-checked against
real operational data later — not generic customer-service topics.

```
BUS_DELAY
BUS_NOT_ARRIVED
BUS_BUNCHING
LONG_SERVICE_GAP
OVER_CROWDING
UNDER_UTILIZATION
VEHICLE_CONDITION
VEHICLE_BREAKDOWN
MAINTENANCE_ISSUE
FUEL_CONSUMPTION
SAFETY_ISSUE
ROUTE_ISSUE
STOP_INFRASTRUCTURE
WEATHER_DISRUPTION
TRAFFIC_DISRUPTION
OTHER
```

### Severity

```
LOW      - Minor issue with limited operational impact.
MEDIUM   - Affects passenger experience or operations but not immediately critical.
HIGH     - Significant operational problem requiring attention.
CRITICAL - Major service disruption or immediate safety/operational risk.
```

### Status

```
NEW       -> observation has been submitted
REVIEWED  -> administrator has examined it
RESOLVED  -> issue has been addressed
```

---

## 4. QR workflow

1. MCTC staff create a QR code record via `POST /qr-codes`, tied to a
   bus number and/or route and/or location.
2. A physical QR sticker is generated (outside this API, using any QR
   library) encoding the URL:
   `http://127.0.0.1:8000/observe/{qr_token}`
3. A person near the bus scans it. Their device opens
   `GET /observe/{qr_token}`, which confirms the QR is valid/active and
   returns the bus/route/location context plus the allowed problem
   categories and severities (this is the data a future frontend form
   would use to render itself).
4. The person fills in what they observed and the client sends
   `POST /observations` with the QR token, problem type, severity,
   description, and when they observed it.
5. The server validates everything, checks for a duplicate submission,
   stores the observation, and returns the new observation's ID.
6. Administrators query `GET /admin/observations` (with optional
   filters), inspect individual records, update their status, and view
   `GET /admin/summary` for aggregate counts.

---

## 5. The one-scan / one-submission rule

**Rule:** the combination `qr_code_id + anonymous_identifier` must be
unique.

- `QR-001` + `DEVICE-001` → allowed
- `QR-001` + `DEVICE-001` again → **rejected (HTTP 409)**
- `QR-001` + `DEVICE-002` → allowed
- `QR-002` + `DEVICE-001` → allowed

This is enforced **twice**:

1. **Application-level check** in `main.py` (`submit_observation`) —
   looks up an existing row with the same `qr_code_id` +
   `anonymous_identifier` before inserting.
2. **Database-level constraint** in `models.py` — a
   `UniqueConstraint("qr_code_id", "anonymous_identifier")` on the
   `observations` table, which also catches race conditions (e.g. two
   near-simultaneous requests) that the application-level check alone
   could miss.

On duplicate, the API returns:

```json
HTTP 409 Conflict
{
    "detail": "An observation has already been submitted for this QR code."
}
```

### ⚠️ Security note (read this)

`anonymous_identifier` is a client-supplied string (e.g. a
locally-generated device ID). **It does not cryptographically prove
that exactly one human submitted.** A user could clear storage, use a
different browser, or otherwise generate a new identifier and submit
again. This is intentional for a lightweight prototype — it discourages
casual accidental double-submission, not determined abuse.

**If MCTC later needs strict one-person-one-submission enforcement,**
a production version would need a stronger mechanism — e.g. phone-OTP
verification, a signed/rotating per-scan token embedded in the QR
itself with short expiry, rate-limiting by IP, or device attestation.
None of that is implemented here by design, to keep the prototype
simple.

---

## 6. Observation vs. Operational Problem — the critical distinction

- **Ground-level observation** (what this system records):
  `"Bus appears heavily overcrowded."` — one person's report, at one
  place, at one time.
- **Operational problem** (what the future analytics layer determines):
  `"Route R101 has recurring peak-hour overcrowding."` — a conclusion
  drawn from many observations *plus* GPS, GTFS, ridership, weather,
  traffic, and fuel/maintenance data over time.

`GET /admin/summary` in this module only counts and groups raw
observations — it never claims to have identified a systemic problem.
That correlation step belongs to the analytics layer described in the
overall MCTC project, not to this QR module.

---

## 7. Future integration points

This schema is intentionally kept simple but integration-friendly:

```
observations
     │
     ├── route_id      → future routes table (GTFS route_id)
     ├── bus_number     → future vehicles table (vehicle_id)
     ├── observed_at    → correlate with GPS pings / scheduled trip times
     └── location        → correlate with stop/geographic data
```

No larger MCTC database is implemented here — only the QR module,
designed so its `route_id`/`bus_number`/`observed_at` fields line up
cleanly with what the larger system will eventually use.

---

## 8. Installation (Windows / VS Code)

Open a terminal in VS Code (View → Terminal) inside the
`mctc_qr_feedback` folder, then:

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it (Windows PowerShell)
.venv\Scripts\Activate.ps1

# (If using Command Prompt instead of PowerShell)
.venv\Scripts\activate.bat

# 3. Install dependencies
pip install -r requirements.txt
```

If PowerShell blocks the activation script, run PowerShell as
Administrator once and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 9. Running the server

```bash
uvicorn main:app --reload
```

You should see output ending with something like:
```
Uvicorn running on http://127.0.0.1:8000
```

- API base URL: `http://127.0.0.1:8000`
- Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`

Open `/docs` in a browser — every endpoint below is testable there by
clicking "Try it out", filling the fields, and clicking "Execute". No
separate frontend or Postman is required for this prototype.

The database file `mctc_feedback.db` is created automatically in the
project folder the first time you run the server (tables are created
on startup from the SQLAlchemy models).

---

## 10. Swagger testing sequence

Go through these in order in `/docs`.

**Test 1 — Health check**
`GET /` → expect:
```json
{"message": "MCTC Ground Observation API is running"}
```

**Test 2 — Create a QR code**
`POST /qr-codes`
```json
{
  "qr_token": "QR-001",
  "bus_number": "AP-XX-1234",
  "route_id": "R101",
  "location": "Inside bus"
}
```

**Test 3 — Get the QR code**
`GET /qr-codes/QR-001` → returns the record you just created.

**Test 4 — Open the observation entry point**
`GET /observe/QR-001` → returns bus/route/location context plus the
list of valid `problem_types` and `severities`.

**Test 5 — Submit an observation**
`POST /observations`
```json
{
  "qr_token": "QR-001",
  "problem_type": "OVER_CROWDING",
  "severity": "HIGH",
  "description": "Bus is extremely crowded during evening peak.",
  "observed_at": "2026-08-30T18:30:00",
  "anonymous_identifier": "DEVICE-001"
}
```
Expect HTTP 201 with `{"message": "...", "observation_id": 1}`.

**Test 6 — Duplicate submission**
Repeat Test 5 exactly (same `qr_token` + same `anonymous_identifier`).
Expect **HTTP 409**:
```json
{"detail": "An observation has already been submitted for this QR code."}
```

**Test 7 — Different identifier, same QR**
Repeat Test 5 with `"anonymous_identifier": "DEVICE-002"`.
Expect success (HTTP 201).

**Test 8 — Different QR, same identifier**
`POST /qr-codes` with `"qr_token": "QR-002", "bus_number": "AP-XX-5678", "route_id": "R102"`.
Then `POST /observations` with `"qr_token": "QR-002"`,
`"anonymous_identifier": "DEVICE-001"`. Expect success.

**Test 9 — List all observations**
`GET /admin/observations` → returns all submitted observations.

**Test 10 — Filter observations**
`GET /admin/observations?problem_type=OVER_CROWDING`
`GET /admin/observations?severity=CRITICAL`
`GET /admin/observations?route_id=R101`

**Test 11 — Summary**
`GET /admin/summary` → returns counts by status/severity and top
problem types.

**Test 12 — Update status**
`PATCH /admin/observations/1/status`
```json
{"status": "REVIEWED"}
```
Then `GET /admin/observations/1` to confirm the change.

---

## 11. Sample realistic test data

Use these via `POST /qr-codes` then `POST /observations` to populate
the database for a demo. **These are made-up test values, not real
MCTC measurements.**

| QR token | Route | Problem type       | Severity |
|----------|-------|---------------------|----------|
| QR-001   | R101  | OVER_CROWDING        | HIGH     |
| QR-001   | R101  | BUS_DELAY            | MEDIUM   |
| QR-002   | R102  | VEHICLE_CONDITION    | HIGH     |
| QR-002   | R102  | MAINTENANCE_ISSUE    | MEDIUM   |
| QR-003   | R103  | SAFETY_ISSUE         | CRITICAL |
| QR-003   | R103  | LONG_SERVICE_GAP     | HIGH     |

(Note: the original brief listed `AC_OR_FAN` as a category — that's not
one of the 16 approved operational categories, so `MAINTENANCE_ISSUE`
is used instead for that row. Add `AC_OR_FAN` as a real enum value
later if MCTC wants vehicle-comfort-equipment tracked as its own
category.)

Each row needs a **different** `anonymous_identifier` per QR token if
submitted from the same test session, or you'll hit the 409 duplicate
check (e.g. `DEVICE-A`, `DEVICE-B`, `DEVICE-C`...).

---

## 12. Common errors and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencies not installed, or venv not activated | Activate `.venv`, then `pip install -r requirements.txt` |
| `uvicorn: command not found` | uvicorn not installed / venv not active | Same as above |
| `404 Not Found` on `/observe/QR-999` | QR token doesn't exist yet | Create it first with `POST /qr-codes` |
| `409 Conflict` on `/observations` | Same QR token + same `anonymous_identifier` submitted twice | Use a different `anonymous_identifier`, or this is expected/correct behavior |
| `400 Bad Request`: "QR code ... is not active" | `is_active` is false for that QR code | This prototype has no endpoint yet to toggle `is_active` — set it directly in the DB, or extend the API |
| `422 Unprocessable Entity` | Invalid enum value (e.g. `"severity": "URGENT"`) or malformed `observed_at` | Use exact enum values from `models.py`; `observed_at` must be ISO 8601, e.g. `2026-08-30T18:30:00` |
| Server starts but `/docs` is blank | Wrong URL or server not actually running | Confirm terminal shows `Uvicorn running on http://127.0.0.1:8000`, then visit `http://127.0.0.1:8000/docs` exactly |
| Changes to code don't take effect | Server not restarted / `--reload` not used | Run with `uvicorn main:app --reload`, or restart manually |
| `sqlite3.OperationalError: database is locked` | Rare with SQLite under concurrent writes | Fine for a prototype/demo; a production system would move to PostgreSQL |

---

## 13. Explicitly out of scope for this prototype

- Authentication/authorization on admin endpoints (clearly labeled
  "prototype — no auth" in the code and Swagger tags).
- A rendered HTML/QR-scanning frontend (endpoints return JSON only;
  a frontend can be built against this API later).
- Actual QR image generation (only the token/URL is handled here).
- Strong identity/anti-abuse enforcement beyond the basic
  one-scan-per-device mechanism described above.
- Any correlation with GPS, GTFS, weather, traffic, fuel, or ridership
  data — that belongs to the separate analytics layer this module
  feeds into.
