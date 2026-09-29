"""
main.py
-------
FastAPI application entry point for the MCTC Ground-Level Operational
Observation System.

IMPORTANT CONTEXT (read before modifying):
This is NOT a passenger complaint system. It is a ground-level
operational OBSERVATION collection tool. A person physically present
near a bus/route scans a QR code and reports what they observe
(e.g. overcrowding, delay, vehicle condition). These observations are
raw evidence that will later be combined with GPS, GTFS, weather,
traffic, ridership, fuel and maintenance data by a separate analytics
layer to identify actual recurring operational problems.

Run with:
    uvicorn main:app --reload
Then open:
    http://127.0.0.1:8000/docs     <- Swagger UI
    http://127.0.0.1:8000          <- Landing page
"""

import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, Query, Request, status
# pyrefly: ignore [missing-import]
from fastapi.responses import HTMLResponse, Response, StreamingResponse
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy.exc import IntegrityError

import models
import schemas
import crud
from database import engine, get_db, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MCTC — Ground-Level Operational Observation API",
    description=(
        "Prototype backend for collecting ground-level operational "
        "observations via QR codes attached to buses/stops. "
        "Part of the TRACE Urban Public Transport Analytics Platform."
    ),
    version="0.2.0",
)


# =======================================================================
# Landing Page
# =======================================================================

@app.get("/", response_class=HTMLResponse, tags=["Health"], include_in_schema=False)
def landing():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCTC — TRACE Observation System</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #e2e8f0;
            }
            .card {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 20px;
                padding: 48px;
                max-width: 560px;
                width: 90%;
                text-align: center;
                backdrop-filter: blur(10px);
            }
            .badge {
                display: inline-block;
                background: #38bdf8;
                color: #0f172a;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 20px;
                letter-spacing: 1px;
                margin-bottom: 20px;
            }
            h1 { font-size: 2rem; font-weight: 700; margin-bottom: 8px; }
            .subtitle { color: #94a3b8; font-size: 0.95rem; margin-bottom: 36px; line-height: 1.6; }
            .links { display: flex; flex-direction: column; gap: 12px; }
            a.btn {
                display: block;
                padding: 14px 20px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: 600;
                font-size: 0.95rem;
                transition: opacity 0.2s;
            }
            a.btn:hover { opacity: 0.85; }
            .btn-primary   { background: #38bdf8; color: #0f172a; }
            .btn-secondary { background: rgba(255,255,255,0.08); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.15); }
            .stats {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 16px;
                margin: 32px 0;
                text-align: center;
            }
            .stat-val { font-size: 1.6rem; font-weight: 700; color: #38bdf8; }
            .stat-lbl { font-size: 0.75rem; color: #64748b; margin-top: 2px; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="badge">TRACE · MCTC</div>
            <h1>🚌 Observation System</h1>
            <p class="subtitle">
                Ground-level operational evidence collection for<br>
                Delhi's DTC bus network.
            </p>
            <div class="links">
                <a class="btn btn-primary" href="/docs">📋 API Documentation (Swagger)</a>
                <a class="btn btn-secondary" href="/admin/summary">📊 Admin Summary (JSON)</a>
                <a class="btn btn-secondary" href="/analytics/by-route?days=30">🛣️ Observations by Route</a>
                <a class="btn btn-secondary" href="/export/observations-csv">⬇️ Export CSV for Fabric</a>
            </div>
            <p style="margin-top:28px; font-size:0.8rem; color:#475569;">
                Field staff: Scan the QR code on the bus or stop<br>to access the observation form.
            </p>
        </div>
    </body>
    </html>
    """)


# =======================================================================
# QR Codes
# =======================================================================

@app.post(
    "/qr-codes",
    response_model=schemas.QRCodeOut,
    status_code=status.HTTP_201_CREATED,
    tags=["QR Codes"],
)
def create_qr_code(qr: schemas.QRCodeCreate, db: Session = Depends(get_db)):
    """
    Register a new QR code for a bus, route or fixed stop location.
    The QR image URL is: /observe/{qr_token}
    """
    if crud.get_qr_code_by_token(db, qr.qr_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"QR token '{qr.qr_token}' already exists.",
        )
    return crud.create_qr_code(db, qr)


@app.get("/qr-codes", response_model=List[schemas.QRCodeOut], tags=["QR Codes"])
def list_qr_codes(db: Session = Depends(get_db)):
    """List all registered QR codes."""
    return db.query(models.QRCode).order_by(models.QRCode.created_at.desc()).all()


@app.get("/qr-codes/{qr_token}", response_model=schemas.QRCodeOut, tags=["QR Codes"])
def get_qr_code(qr_token: str, db: Session = Depends(get_db)):
    db_qr = crud.get_qr_code_by_token(db, qr_token)
    if db_qr is None:
        raise HTTPException(status_code=404, detail=f"QR code '{qr_token}' not found.")
    return db_qr


@app.get("/qr-codes/{qr_token}/image", tags=["QR Codes"])
def get_qr_image(qr_token: str, request: Request, db: Session = Depends(get_db)):
    """
    Returns a scannable PNG QR code image for the given token.
    The QR encodes the full /observe/{token} URL.
    """
    import qrcode

    db_qr = crud.get_qr_code_by_token(db, qr_token)
    if db_qr is None:
        raise HTTPException(status_code=404, detail=f"QR code '{qr_token}' not found.")

    base_url = str(request.base_url).rstrip("/")
    observe_url = f"{base_url}/observe/{qr_token}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(observe_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to PIL Image to ensure PNG save works
    pil_img = img.get_image() if hasattr(img, 'get_image') else img._img
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


# =======================================================================
# Observation Entry (HTML form — what opens when QR is scanned)
# =======================================================================

@app.get("/observe/{qr_token}", response_class=HTMLResponse, tags=["Observation Entry"])
def observe_entry_point(qr_token: str, db: Session = Depends(get_db)):
    """
    URL encoded inside the physical QR code.
    Returns a mobile-friendly HTML form for field staff.
    """
    db_qr = crud.get_qr_code_by_token(db, qr_token)
    if db_qr is None:
        return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:40px;">
        <h2>❌ Invalid QR Code</h2>
        <p>This QR code is not registered in the TRACE system.</p>
        </body></html>
        """, status_code=404)

    if not db_qr.is_active:
        return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:40px;">
        <h2>⚠️ QR Code Inactive</h2>
        <p>This QR code has been deactivated. Please contact operations.</p>
        </body></html>
        """, status_code=400)

    problem_options = "".join(
        f'<option value="{p.value}">{p.value.replace("_", " ").title()}</option>'
        for p in models.ProblemType
    )
    severity_options = "".join(
        f'<option value="{s.value}">{s.value.capitalize()}</option>'
        for s in models.Severity
    )

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TRACE — Report Observation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                min-height: 100vh;
                display: flex;
                align-items: flex-start;
                justify-content: center;
                padding: 24px 16px;
            }}
            .container {{ width: 100%; max-width: 460px; }}
            .header {{
                background: linear-gradient(135deg, #1e40af, #0ea5e9);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .header h2 {{ font-size: 1.3rem; font-weight: 700; }}
            .header .meta {{ font-size: 0.82rem; opacity: 0.85; margin-top: 6px; }}
            .card {{
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 16px;
            }}
            label {{
                display: block;
                font-size: 0.82rem;
                font-weight: 600;
                color: #94a3b8;
                margin-bottom: 6px;
                margin-top: 16px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            label:first-child {{ margin-top: 0; }}
            select, textarea {{
                width: 100%;
                padding: 10px 14px;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 0.95rem;
                outline: none;
                transition: border-color 0.2s;
            }}
            select:focus, textarea:focus {{ border-color: #38bdf8; }}
            textarea {{ resize: vertical; min-height: 80px; }}
            .severity-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }}
            .sev-btn {{
                padding: 10px;
                border: 2px solid #334155;
                border-radius: 8px;
                background: #0f172a;
                color: #94a3b8;
                font-size: 0.85rem;
                font-weight: 600;
                cursor: pointer;
                text-align: center;
                transition: all 0.15s;
            }}
            .sev-btn:hover {{ border-color: #38bdf8; color: #38bdf8; }}
            .sev-btn.selected {{ border-color: #38bdf8; background: #0c4a6e; color: #38bdf8; }}
            .sev-btn.LOW.selected    {{ border-color: #4ade80; background: #052e16; color: #4ade80; }}
            .sev-btn.MEDIUM.selected {{ border-color: #facc15; background: #422006; color: #facc15; }}
            .sev-btn.HIGH.selected   {{ border-color: #fb923c; background: #431407; color: #fb923c; }}
            .sev-btn.CRITICAL.selected {{ border-color: #f87171; background: #450a0a; color: #f87171; }}
            #submitBtn {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #1e40af, #0ea5e9);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 700;
                cursor: pointer;
                margin-top: 8px;
                transition: opacity 0.2s;
            }}
            #submitBtn:hover {{ opacity: 0.9; }}
            #submitBtn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            .footer {{ text-align: center; font-size: 0.75rem; color: #475569; margin-top: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🚌 Report Observation</h2>
                <div class="meta">
                    Bus: <b>{db_qr.bus_number or "—"}</b> &nbsp;·&nbsp;
                    Route: <b>{db_qr.route_id or "—"}</b> &nbsp;·&nbsp;
                    {db_qr.location or ""}
                </div>
            </div>

            <div class="card">
                <label>Problem Type</label>
                <select id="problem_type">{problem_options}</select>

                <label>Severity</label>
                <div class="severity-grid">
                    <div class="sev-btn LOW"      onclick="setSeverity('LOW')">🟢 Low</div>
                    <div class="sev-btn MEDIUM"   onclick="setSeverity('MEDIUM')">🟡 Medium</div>
                    <div class="sev-btn HIGH"     onclick="setSeverity('HIGH')">🟠 High</div>
                    <div class="sev-btn CRITICAL" onclick="setSeverity('CRITICAL')">🔴 Critical</div>
                </div>
                <input type="hidden" id="severity" value="MEDIUM">

                <label>Description <span style="font-weight:400;color:#64748b">(optional)</span></label>
                <textarea id="description" maxlength="1000"
                    placeholder="What exactly did you observe?"></textarea>
            </div>

            <button id="submitBtn" onclick="submitObs()">Submit Observation</button>
            <div class="footer">TRACE · MCTC Ground Observation System · v0.2</div>
        </div>

        <script>
        // Pre-select MEDIUM severity
        setSeverity('MEDIUM');

        function setSeverity(val) {{
            document.getElementById('severity').value = val;
            document.querySelectorAll('.sev-btn').forEach(b => b.classList.remove('selected'));
            document.querySelector('.sev-btn.' + val).classList.add('selected');
        }}

        async function submitObs() {{
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.textContent = 'Submitting…';

            // Get geolocation if available
            let lat = null, lon = null;
            try {{
                const pos = await new Promise((res, rej) =>
                    navigator.geolocation.getCurrentPosition(res, rej, {{timeout: 3000}})
                );
                lat = pos.coords.latitude;
                lon = pos.coords.longitude;
            }} catch(e) {{}}

            const payload = {{
                qr_token:             "{qr_token}",
                problem_type:         document.getElementById('problem_type').value,
                severity:             document.getElementById('severity').value,
                description:          document.getElementById('description').value || null,
                observed_at:          new Date().toISOString(),
                latitude:             lat,
                longitude:            lon,
                anonymous_identifier: crypto.randomUUID()
            }};

            try {{
                const res = await fetch('/observations', {{
                    method:  'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body:    JSON.stringify(payload)
                }});
                const data = await res.json();
                if (res.ok) {{
                    document.body.innerHTML = `
                        <div style="font-family:sans-serif;text-align:center;padding:60px 20px;color:#e2e8f0;background:#0f172a;min-height:100vh;display:flex;align-items:center;justify-content:center;">
                        <div>
                            <div style="font-size:4rem">✅</div>
                            <h2 style="margin:16px 0 8px;font-size:1.4rem;">Observation Submitted</h2>
                            <p style="color:#94a3b8">Thank you. Your report has been recorded.</p>
                            <p style="color:#475569;font-size:0.8rem;margin-top:12px">ID: ${{data.observation_id}}</p>
                        </div></div>`;
                }} else if (res.status === 409) {{
                    btn.disabled = false;
                    btn.textContent = 'Submit Observation';
                    alert('You have already submitted a report for this bus in the last hour.');
                }} else {{
                    throw new Error(data.detail || 'Submission failed');
                }}
            }} catch(e) {{
                btn.disabled = false;
                btn.textContent = 'Submit Observation';
                alert('Error: ' + e.message);
            }}
        }}
        </script>
    </body>
    </html>
    """)


# =======================================================================
# Submit Observation
# =======================================================================

@app.post(
    "/observations",
    response_model=schemas.ObservationSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Observations"],
)
def submit_observation(obs: schemas.ObservationCreate, db: Session = Depends(get_db)):
    """
    Submit a ground-level operational observation.
    Multiple different people CAN submit for the same QR code.
    Same person is limited to once per 60 minutes per QR code.
    """
    db_qr = crud.get_qr_code_by_token(db, obs.qr_token)
    if db_qr is None:
        raise HTTPException(status_code=404, detail=f"QR code '{obs.qr_token}' not found.")
    if not db_qr.is_active:
        raise HTTPException(status_code=400, detail=f"QR code '{obs.qr_token}' is not active.")

    # Time-window duplicate check (60 min per identifier per QR)
    recent = crud.check_recent_duplicate(db, db_qr.id, obs.anonymous_identifier)
    if recent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted an observation for this bus in the last hour.",
        )

    db_obs = crud.create_observation(db, obs, db_qr)
    return schemas.ObservationSubmitResponse(
        message="Operational observation submitted successfully",
        observation_id=db_obs.id,
    )


# =======================================================================
# Admin Endpoints
# =======================================================================

@app.get(
    "/admin/observations",
    response_model=List[schemas.ObservationOut],
    tags=["Admin"],
)
def list_observations(
    problem_type: Optional[models.ProblemType] = Query(None),
    severity:     Optional[models.Severity]    = Query(None),
    status_filter:Optional[models.ObservationStatus] = Query(None, alias="status"),
    route_id:     Optional[str] = Query(None),
    bus_number:   Optional[str] = Query(None),
    days:         Optional[int] = Query(None, description="Filter to last N days"),
    skip:         int           = Query(0),
    limit:        int           = Query(200, le=1000),
    db: Session = Depends(get_db),
):
    """Admin: list observations with filters. Add ?days=7 for recent only."""
    return crud.get_observations(
        db,
        problem_type=problem_type,
        severity=severity,
        status=status_filter,
        route_id=route_id,
        bus_number=bus_number,
        days=days,
        skip=skip,
        limit=limit,
    )


@app.get("/admin/observations/{observation_id}", response_model=schemas.ObservationOut, tags=["Admin"])
def get_observation(observation_id: int, db: Session = Depends(get_db)):
    db_obs = crud.get_observation(db, observation_id)
    if db_obs is None:
        raise HTTPException(status_code=404, detail=f"Observation {observation_id} not found.")
    return db_obs


@app.patch("/admin/observations/{observation_id}/status", response_model=schemas.ObservationOut, tags=["Admin"])
def update_observation_status(
    observation_id: int,
    update: schemas.ObservationStatusUpdate,
    db: Session = Depends(get_db),
):
    db_obs = crud.update_observation_status(db, observation_id, update.status)
    if db_obs is None:
        raise HTTPException(status_code=404, detail=f"Observation {observation_id} not found.")
    return db_obs


@app.get("/admin/summary", response_model=schemas.AdminSummary, tags=["Admin"])
def admin_summary(db: Session = Depends(get_db)):
    return crud.get_summary(db)


# =======================================================================
# Analytics Endpoints (for Power BI / TRACE dashboards)
# =======================================================================

@app.get("/analytics/by-route", tags=["Analytics"])
def observations_by_route(
    days: int = Query(30, description="Look-back window in days"),
    db: Session = Depends(get_db),
):
    """
    Top problem routes — feed this into the Customer Experience
    Head dashboard in Power BI.
    """
    results = crud.get_observations_by_route(db, days=days)
    return [
        {
            "route_id":    r.route_id,
            "problem_type": r.problem_type,
            "severity":    r.severity,
            "count":       r.count,
        }
        for r in results
    ]


@app.get("/analytics/summary-by-type", tags=["Analytics"])
def summary_by_problem_type(
    days: int = Query(30),
    db: Session = Depends(get_db),
):
    """Problem type distribution — for the Operations Head dashboard."""
    results = crud.get_summary_by_problem_type(db, days=days)
    return [
        {"problem_type": r.problem_type, "severity": r.severity, "count": r.count}
        for r in results
    ]


# =======================================================================
# Admin Dashboard Frontend
# =======================================================================

@app.get("/admin-dashboard", response_class=HTMLResponse, tags=["Admin"], include_in_schema=False)
def admin_dashboard():
    """
    Full admin dashboard UI — live data from the API.
    For: Depot Manager, Route Planning Manager, Customer Experience Head,
         Fleet & Maintenance Manager, Head of Operations Analytics.
    """
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRACE MCTC — Admin Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg:      #0a0f1e;
            --surface: #111827;
            --border:  #1f2937;
            --text:    #e2e8f0;
            --muted:   #64748b;
            --accent:  #38bdf8;
            --green:   #4ade80;
            --yellow:  #facc15;
            --orange:  #fb923c;
            --red:     #f87171;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

        /* ── Sidebar ── */
        .layout { display: flex; min-height: 100vh; }
        .sidebar {
            width: 220px; flex-shrink: 0;
            background: var(--surface);
            border-right: 1px solid var(--border);
            padding: 24px 0;
            position: fixed; top: 0; left: 0; bottom: 0;
            display: flex; flex-direction: column;
        }
        .logo { padding: 0 20px 24px; border-bottom: 1px solid var(--border); }
        .logo h1 { font-size: 1.2rem; font-weight: 800; color: var(--accent); }
        .logo p { font-size: 0.7rem; color: var(--muted); margin-top: 2px; }
        .nav { padding: 16px 0; flex: 1; }
        .nav-item {
            display: flex; align-items: center; gap: 10px;
            padding: 10px 20px; cursor: pointer;
            color: var(--muted); font-size: 0.875rem; font-weight: 500;
            transition: all 0.15s; border-left: 3px solid transparent;
        }
        .nav-item:hover { color: var(--text); background: rgba(255,255,255,0.03); }
        .nav-item.active { color: var(--accent); border-left-color: var(--accent); background: rgba(56,189,248,0.06); }
        .sidebar-footer { padding: 16px 20px; border-top: 1px solid var(--border); font-size: 0.7rem; color: var(--muted); }

        /* ── Main ── */
        .main { margin-left: 220px; flex: 1; padding: 28px; }
        .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
        .topbar h2 { font-size: 1.4rem; font-weight: 700; }
        .topbar .actions { display: flex; gap: 10px; }
        .btn {
            padding: 8px 16px; border-radius: 8px; border: none;
            font-size: 0.8rem; font-weight: 600; cursor: pointer;
            transition: opacity 0.2s; display: flex; align-items: center; gap: 6px;
        }
        .btn:hover { opacity: 0.85; }
        .btn-primary { background: var(--accent); color: #0a0f1e; }
        .btn-ghost   { background: rgba(255,255,255,0.07); color: var(--text); border: 1px solid var(--border); }

        /* ── KPI Cards ── */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .kpi {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 14px; padding: 18px;
        }
        .kpi-label { font-size: 0.72rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-val   { font-size: 2rem; font-weight: 800; margin: 6px 0 0; }
        .kpi-sub   { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }
        .c-blue   { color: var(--accent); }
        .c-green  { color: var(--green); }
        .c-yellow { color: var(--yellow); }
        .c-orange { color: var(--orange); }
        .c-red    { color: var(--red); }

        /* ── Charts Row ── */
        .charts-row { display: grid; grid-template-columns: 1fr 1.6fr; gap: 16px; margin-bottom: 24px; }
        .chart-card {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 14px; padding: 20px;
        }
        .chart-card h3 { font-size: 0.875rem; font-weight: 700; margin-bottom: 16px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .chart-wrap { position: relative; height: 220px; }

        /* ── Filters ── */
        .filters {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 14px; padding: 16px;
            display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px;
            align-items: flex-end;
        }
        .filter-group { display: flex; flex-direction: column; gap: 4px; }
        .filter-group label { font-size: 0.72rem; color: var(--muted); font-weight: 600; text-transform: uppercase; }
        select.filter-sel, input.filter-inp {
            background: #0a0f1e; border: 1px solid var(--border); border-radius: 7px;
            color: var(--text); padding: 7px 10px; font-size: 0.82rem; outline: none;
            transition: border-color 0.2s; min-width: 130px;
        }
        select.filter-sel:focus, input.filter-inp:focus { border-color: var(--accent); }

        /* ── Table ── */
        .table-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }
        .table-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .table-header h3 { font-size: 0.875rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
        th { padding: 10px 16px; text-align: left; font-size: 0.72rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
        td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: top; }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: rgba(255,255,255,0.02); }
        .badge {
            display: inline-block; padding: 3px 8px; border-radius: 20px;
            font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        }
        .badge-NEW      { background: rgba(56,189,248,0.15); color: var(--accent); }
        .badge-REVIEWED { background: rgba(250,204,21,0.15); color: var(--yellow); }
        .badge-RESOLVED { background: rgba(74,222,128,0.15); color: var(--green); }
        .badge-LOW      { background: rgba(74,222,128,0.12); color: var(--green); }
        .badge-MEDIUM   { background: rgba(250,204,21,0.12); color: var(--yellow); }
        .badge-HIGH     { background: rgba(251,146,60,0.12); color: var(--orange); }
        .badge-CRITICAL { background: rgba(248,113,113,0.18); color: var(--red); }
        .desc-cell { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--muted); }
        .status-sel {
            background: #0a0f1e; border: 1px solid var(--border); border-radius: 6px;
            color: var(--text); padding: 4px 8px; font-size: 0.75rem; cursor: pointer;
        }
        .empty { text-align: center; padding: 48px; color: var(--muted); font-size: 0.875rem; }
        .spinner { display: inline-block; width: 20px; height: 20px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.6s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Page sections ── */
        .page { display: none; }
        .page.active { display: block; }

        /* ── QR Manager ── */
        .form-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 24px; margin-bottom: 16px; }
        .form-card h3 { font-size: 0.875rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        .form-group label { font-size: 0.75rem; font-weight: 600; color: var(--muted); text-transform: uppercase; }
        .form-group input {
            background: #0a0f1e; border: 1px solid var(--border); border-radius: 8px;
            color: var(--text); padding: 9px 12px; font-size: 0.875rem; outline: none;
            transition: border-color 0.2s;
        }
        .form-group input:focus { border-color: var(--accent); }
        .qr-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
        .qr-item { background: #0a0f1e; border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
        .qr-token { font-size: 0.8rem; font-weight: 700; color: var(--accent); margin-bottom: 6px; }
        .qr-meta  { font-size: 0.75rem; color: var(--muted); line-height: 1.6; }
        .qr-url   { font-size: 0.7rem; color: var(--muted); margin-top: 8px; word-break: break-all; }

        @media (max-width: 900px) {
            .sidebar { display: none; }
            .main { margin-left: 0; padding: 16px; }
            .charts-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="layout">

    <!-- Sidebar -->
    <nav class="sidebar">
        <div class="logo">
            <h1>🚌 TRACE</h1>
            <p>MCTC Observation System</p>
        </div>
        <div class="nav">
            <div class="nav-item active" onclick="showPage('dashboard')">📊 Dashboard</div>
            <div class="nav-item" onclick="showPage('observations')">📋 Observations</div>
            <div class="nav-item" onclick="showPage('analytics')">📈 Analytics</div>
            <div class="nav-item" onclick="showPage('qr-manager')">🔲 QR Manager</div>
        </div>
        <div class="sidebar-footer">v0.2 · TRACE Project</div>
    </nav>

    <!-- Main Content -->
    <main class="main">

        <!-- ── DASHBOARD PAGE ── -->
        <div id="page-dashboard" class="page active">
            <div class="topbar">
                <h2>Operations Dashboard</h2>
                <div class="actions">
                    <button class="btn btn-ghost" onclick="loadDashboard()">🔄 Refresh</button>
                    <a href="/export/observations-csv?days=7" class="btn btn-primary">⬇ Export CSV</a>
                </div>
            </div>

            <div class="kpi-grid" id="kpi-grid">
                <div class="kpi"><div class="kpi-label">Total</div><div class="kpi-val c-blue" id="k-total">—</div><div class="kpi-sub">observations</div></div>
                <div class="kpi"><div class="kpi-label">New</div><div class="kpi-val c-accent" id="k-new" style="color:var(--accent)">—</div><div class="kpi-sub">needs review</div></div>
                <div class="kpi"><div class="kpi-label">Reviewed</div><div class="kpi-val c-yellow" id="k-reviewed">—</div><div class="kpi-sub">in progress</div></div>
                <div class="kpi"><div class="kpi-label">Resolved</div><div class="kpi-val c-green" id="k-resolved">—</div><div class="kpi-sub">closed</div></div>
                <div class="kpi"><div class="kpi-label">High</div><div class="kpi-val c-orange" id="k-high">—</div><div class="kpi-sub">priority</div></div>
                <div class="kpi"><div class="kpi-label">Critical</div><div class="kpi-val c-red" id="k-critical">—</div><div class="kpi-sub">urgent</div></div>
            </div>

            <div class="charts-row">
                <div class="chart-card">
                    <h3>Problem Types</h3>
                    <div class="chart-wrap"><canvas id="chart-donut"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>Top Problem Routes</h3>
                    <div class="chart-wrap"><canvas id="chart-routes"></canvas></div>
                </div>
            </div>

            <!-- Recent observations mini-table -->
            <div class="table-card">
                <div class="table-header">
                    <h3>Recent Observations</h3>
                    <button class="btn btn-ghost" onclick="showPage('observations')">View all →</button>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead><tr>
                            <th>ID</th><th>Route</th><th>Bus</th>
                            <th>Problem</th><th>Severity</th><th>Status</th><th>Observed At</th>
                        </tr></thead>
                        <tbody id="recent-tbody"><tr><td colspan="7" class="empty"><div class="spinner"></div></td></tr></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ── OBSERVATIONS PAGE ── -->
        <div id="page-observations" class="page">
            <div class="topbar">
                <h2>All Observations</h2>
                <div class="actions">
                    <button class="btn btn-ghost" onclick="loadObservations()">🔄 Refresh</button>
                    <a id="export-link" href="/export/observations-csv?days=30" class="btn btn-primary">⬇ Export CSV</a>
                </div>
            </div>

            <div class="filters">
                <div class="filter-group">
                    <label>Problem Type</label>
                    <select class="filter-sel" id="f-type" onchange="loadObservations()">
                        <option value="">All</option>
                        <option>BUS_DELAY</option><option>BUS_NOT_ARRIVED</option>
                        <option>BUS_BUNCHING</option><option>LONG_SERVICE_GAP</option>
                        <option>OVER_CROWDING</option><option>UNDER_UTILIZATION</option>
                        <option>VEHICLE_CONDITION</option><option>VEHICLE_BREAKDOWN</option>
                        <option>MAINTENANCE_ISSUE</option><option>FUEL_CONSUMPTION</option>
                        <option>SAFETY_ISSUE</option><option>ROUTE_ISSUE</option>
                        <option>STOP_INFRASTRUCTURE</option><option>WEATHER_DISRUPTION</option>
                        <option>TRAFFIC_DISRUPTION</option><option>OTHER</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Severity</label>
                    <select class="filter-sel" id="f-severity" onchange="loadObservations()">
                        <option value="">All</option>
                        <option>LOW</option><option>MEDIUM</option>
                        <option>HIGH</option><option>CRITICAL</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Status</label>
                    <select class="filter-sel" id="f-status" onchange="loadObservations()">
                        <option value="">All</option>
                        <option>NEW</option><option>REVIEWED</option><option>RESOLVED</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Route ID</label>
                    <input class="filter-inp" id="f-route" placeholder="e.g. 628STLUP" onchange="loadObservations()">
                </div>
                <div class="filter-group">
                    <label>Days Back</label>
                    <select class="filter-sel" id="f-days" onchange="loadObservations()">
                        <option value="">All time</option>
                        <option value="1">Last 24 hrs</option>
                        <option value="7" selected>Last 7 days</option>
                        <option value="30">Last 30 days</option>
                    </select>
                </div>
            </div>

            <div class="table-card">
                <div class="table-header">
                    <h3 id="obs-count">Observations</h3>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead><tr>
                            <th>ID</th><th>Route</th><th>Bus</th>
                            <th>Problem</th><th>Severity</th><th>Description</th>
                            <th>Status</th><th>Observed At</th>
                        </tr></thead>
                        <tbody id="obs-tbody"><tr><td colspan="8" class="empty"><div class="spinner"></div></td></tr></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ── ANALYTICS PAGE ── -->
        <div id="page-analytics" class="page">
            <div class="topbar">
                <h2>Analytics</h2>
                <div class="actions">
                    <select class="filter-sel" id="a-days" onchange="loadAnalytics()">
                        <option value="7">Last 7 days</option>
                        <option value="30" selected>Last 30 days</option>
                        <option value="90">Last 90 days</option>
                    </select>
                    <button class="btn btn-ghost" onclick="loadAnalytics()">🔄 Refresh</button>
                </div>
            </div>

            <div class="charts-row" style="grid-template-columns:1fr 1fr;">
                <div class="chart-card">
                    <h3>Observations by Problem Type</h3>
                    <div class="chart-wrap"><canvas id="chart-type-bar"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>Severity Distribution</h3>
                    <div class="chart-wrap"><canvas id="chart-sev-donut"></canvas></div>
                </div>
            </div>

            <div class="chart-card" style="margin-bottom:16px">
                <h3>Top Routes by Observation Count</h3>
                <div class="chart-wrap" style="height:280px;"><canvas id="chart-route-bar"></canvas></div>
            </div>

            <div class="table-card">
                <div class="table-header"><h3>Route Problem Breakdown</h3></div>
                <div class="table-wrap">
                    <table>
                        <thead><tr><th>Route</th><th>Problem Type</th><th>Severity</th><th>Count</th></tr></thead>
                        <tbody id="analytics-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ── QR MANAGER PAGE ── -->
        <div id="page-qr-manager" class="page">
            <div class="topbar"><h2>QR Code Manager</h2></div>

            <div class="form-card">
                <h3>Register New QR Code</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label>QR Token *</label>
                        <input id="qr-token" placeholder="e.g. BUS-DL1PD5222">
                    </div>
                    <div class="form-group">
                        <label>Bus Number</label>
                        <input id="qr-bus" placeholder="e.g. DL1PD5222">
                    </div>
                    <div class="form-group">
                        <label>Route ID</label>
                        <input id="qr-route" placeholder="e.g. 628STLUP">
                    </div>
                    <div class="form-group">
                        <label>Location</label>
                        <input id="qr-location" placeholder="e.g. Inside bus - rear door">
                    </div>
                </div>
                <button class="btn btn-primary" style="margin-top:16px" onclick="createQR()">+ Register QR Code</button>
                <span id="qr-msg" style="margin-left:12px;font-size:0.8rem;"></span>
            </div>

            <div class="form-card">
                <h3>Registered QR Codes</h3>
                <div id="qr-list" class="qr-list"><div class="spinner"></div></div>
            </div>
        </div>

    </main>
</div>

<script>
// ── Chart instances (to destroy before re-rendering) ──
let donutChart, routesChart, typeBarChart, sevDonutChart, routeBarChart;

// ── Page navigation ──
function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + name).classList.add('active');
    event.target.classList.add('active');

    if (name === 'dashboard')    loadDashboard();
    if (name === 'observations') loadObservations();
    if (name === 'analytics')    loadAnalytics();
    if (name === 'qr-manager')   loadQRCodes();
}

// ── Helpers ──
function fmt(dt) {
    if (!dt) return '—';
    return new Date(dt).toLocaleString('en-IN', {timeZone:'Asia/Kolkata', hour12:false, month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'});
}
function badge(val, prefix='') {
    return `<span class="badge badge-${val}">${val}</span>`;
}

// ── DASHBOARD ──
async function loadDashboard() {
    // KPIs
    const s = await fetch('/admin/summary').then(r => r.json());
    document.getElementById('k-total').textContent    = s.total_observations;
    document.getElementById('k-new').textContent      = s.new_observations;
    document.getElementById('k-reviewed').textContent = s.reviewed_observations;
    document.getElementById('k-resolved').textContent = s.resolved_observations;
    document.getElementById('k-high').textContent     = s.high_priority;
    document.getElementById('k-critical').textContent = s.critical_priority;

    // Donut chart — problem types
    const labels = s.top_problem_types.map(x => x.problem_type.replace(/_/g,' '));
    const counts = s.top_problem_types.map(x => x.count);
    const colors = ['#38bdf8','#4ade80','#facc15','#fb923c','#f87171','#a78bfa','#34d399','#60a5fa'];
    if (donutChart) donutChart.destroy();
    donutChart = new Chart(document.getElementById('chart-donut'), {
        type: 'doughnut',
        data: { labels, datasets: [{ data: counts, backgroundColor: colors, borderWidth: 0, hoverOffset: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 12, padding: 8 } } } }
    });

    // Bar chart — top routes
    const r = await fetch('/analytics/by-route?days=30').then(r => r.json());
    const routeMap = {};
    r.forEach(x => { routeMap[x.route_id] = (routeMap[x.route_id] || 0) + x.count; });
    const topRoutes = Object.entries(routeMap).sort((a,b)=>b[1]-a[1]).slice(0,10);
    if (routesChart) routesChart.destroy();
    routesChart = new Chart(document.getElementById('chart-routes'), {
        type: 'bar',
        data: {
            labels: topRoutes.map(x => x[0] || 'Unknown'),
            datasets: [{ data: topRoutes.map(x => x[1]), backgroundColor: '#38bdf8', borderRadius: 6, borderSkipped: false }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1f2937' } },
                y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1f2937' }, beginAtZero: true }
            }
        }
    });

    // Recent obs
    const obs = await fetch('/admin/observations?limit=10').then(r => r.json());
    const tb = document.getElementById('recent-tbody');
    if (!obs.length) { tb.innerHTML = '<tr><td colspan="7" class="empty">No observations yet.</td></tr>'; return; }
    tb.innerHTML = obs.map(o => `
        <tr>
            <td style="color:var(--muted)">#${o.id}</td>
            <td>${o.route_id || '—'}</td>
            <td>${o.bus_number || '—'}</td>
            <td style="font-size:0.78rem">${(o.problem_type||'').replace(/_/g,' ')}</td>
            <td>${badge(o.severity)}</td>
            <td>${badge(o.status)}</td>
            <td style="color:var(--muted);white-space:nowrap">${fmt(o.observed_at)}</td>
        </tr>`).join('');
}

// ── OBSERVATIONS ──
async function loadObservations() {
    const type     = document.getElementById('f-type').value;
    const severity = document.getElementById('f-severity').value;
    const status   = document.getElementById('f-status').value;
    const route    = document.getElementById('f-route').value;
    const days     = document.getElementById('f-days').value;
    let url = '/admin/observations?limit=500';
    if (type)     url += '&problem_type=' + type;
    if (severity) url += '&severity=' + severity;
    if (status)   url += '&status=' + status;
    if (route)    url += '&route_id=' + route;
    if (days)     url += '&days=' + days;

    document.getElementById('obs-tbody').innerHTML = '<tr><td colspan="8" class="empty"><div class="spinner"></div></td></tr>';
    const obs = await fetch(url).then(r => r.json());
    document.getElementById('obs-count').textContent = `Observations (${obs.length})`;

    if (!obs.length) {
        document.getElementById('obs-tbody').innerHTML = '<tr><td colspan="8" class="empty">No observations match your filters.</td></tr>';
        return;
    }
    document.getElementById('obs-tbody').innerHTML = obs.map(o => `
        <tr>
            <td style="color:var(--muted)">#${o.id}</td>
            <td>${o.route_id || '—'}</td>
            <td>${o.bus_number || '—'}</td>
            <td style="font-size:0.78rem">${(o.problem_type||'').replace(/_/g,' ')}</td>
            <td>${badge(o.severity)}</td>
            <td class="desc-cell" title="${o.description||''}">${o.description || '—'}</td>
            <td>
                <select class="status-sel" onchange="updateStatus(${o.id}, this.value)">
                    <option ${o.status==='NEW'?'selected':''}>NEW</option>
                    <option ${o.status==='REVIEWED'?'selected':''}>REVIEWED</option>
                    <option ${o.status==='RESOLVED'?'selected':''}>RESOLVED</option>
                </select>
            </td>
            <td style="color:var(--muted);white-space:nowrap">${fmt(o.observed_at)}</td>
        </tr>`).join('');
}

async function updateStatus(id, newStatus) {
    await fetch('/admin/observations/' + id + '/status', {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({status: newStatus})
    });
}

// ── ANALYTICS ──
async function loadAnalytics() {
    const days = document.getElementById('a-days').value;

    const byType  = await fetch('/analytics/summary-by-type?days=' + days).then(r => r.json());
    const byRoute = await fetch('/analytics/by-route?days=' + days).then(r => r.json());

    // Problem type bar
    const typeMap = {};
    byType.forEach(x => { typeMap[x.problem_type] = (typeMap[x.problem_type]||0) + x.count; });
    const typesSorted = Object.entries(typeMap).sort((a,b)=>b[1]-a[1]);
    if (typeBarChart) typeBarChart.destroy();
    typeBarChart = new Chart(document.getElementById('chart-type-bar'), {
        type: 'bar',
        data: {
            labels: typesSorted.map(x => x[0].replace(/_/g,' ')),
            datasets: [{ data: typesSorted.map(x=>x[1]), backgroundColor: '#38bdf8', borderRadius: 5, borderSkipped: false }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks:{color:'#94a3b8',font:{size:10}}, grid:{color:'#1f2937'}, beginAtZero:true },
                y: { ticks:{color:'#94a3b8',font:{size:9}}, grid:{color:'#1f2937'} }
            }
        }
    });

    // Severity donut
    const sevMap = {LOW:0,MEDIUM:0,HIGH:0,CRITICAL:0};
    byType.forEach(x => { if (sevMap[x.severity]!==undefined) sevMap[x.severity]+=x.count; });
    if (sevDonutChart) sevDonutChart.destroy();
    sevDonutChart = new Chart(document.getElementById('chart-sev-donut'), {
        type: 'doughnut',
        data: {
            labels: ['Low','Medium','High','Critical'],
            datasets: [{ data: Object.values(sevMap), backgroundColor: ['#4ade80','#facc15','#fb923c','#f87171'], borderWidth: 0, hoverOffset: 6 }]
        },
        options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom',labels:{color:'#94a3b8',font:{size:11},boxWidth:14}}} }
    });

    // Route bar
    const routeMap = {};
    byRoute.forEach(x => { routeMap[x.route_id||(x.route_id||'Unknown')] = (routeMap[x.route_id]||0)+x.count; });
    const topRoutes = Object.entries(routeMap).sort((a,b)=>b[1]-a[1]).slice(0,12);
    if (routeBarChart) routeBarChart.destroy();
    routeBarChart = new Chart(document.getElementById('chart-route-bar'), {
        type: 'bar',
        data: {
            labels: topRoutes.map(x=>x[0]||'Unknown'),
            datasets: [{ data: topRoutes.map(x=>x[1]), backgroundColor: '#a78bfa', borderRadius: 6, borderSkipped: false }]
        },
        options: {
            responsive:true, maintainAspectRatio:false,
            plugins:{legend:{display:false}},
            scales:{
                x:{ticks:{color:'#94a3b8',font:{size:10}},grid:{color:'#1f2937'}},
                y:{ticks:{color:'#94a3b8',font:{size:10}},grid:{color:'#1f2937'},beginAtZero:true}
            }
        }
    });

    // Table
    document.getElementById('analytics-tbody').innerHTML = byRoute.map(r => `
        <tr>
            <td>${r.route_id||'Unknown'}</td>
            <td style="font-size:0.78rem">${(r.problem_type||'').replace(/_/g,' ')}</td>
            <td>${badge(r.severity)}</td>
            <td style="font-weight:700;color:var(--accent)">${r.count}</td>
        </tr>`).join('') || '<tr><td colspan="4" class="empty">No data for this period.</td></tr>';
}

// ── QR MANAGER ──
async function loadQRCodes() {
    const el = document.getElementById('qr-list');
    el.innerHTML = '<div class="spinner"></div>';

    try {
        const qrCodes = await fetch('/qr-codes').then(r => r.json());

        if (!qrCodes.length) {
            el.innerHTML = `
                <div class="qr-item" style="grid-column:1/-1">
                    <div class="qr-token">📱 No QR codes registered yet</div>
                    <div class="qr-meta">Use the form above to register your first QR code.</div>
                </div>`;
            return;
        }

        el.innerHTML = qrCodes.map(qr => `
            <div class="qr-item">
                <div style="text-align:center;margin-bottom:12px">
                    <img
                        src="/qr-codes/${qr.qr_token}/image"
                        alt="QR for ${qr.qr_token}"
                        style="width:160px;height:160px;border-radius:8px;border:4px solid white;"
                        onerror="this.style.display='none'"
                    >
                </div>
                <div class="qr-token">🔲 ${qr.qr_token}</div>
                <div class="qr-meta">
                    Bus: <b>${qr.bus_number || '—'}</b><br>
                    Route: <b>${qr.route_id || '—'}</b><br>
                    Location: ${qr.location || '—'}<br>
                    Status: <b style="color:${qr.is_active ? '#4ade80' : '#f87171'}">${qr.is_active ? 'Active' : 'Inactive'}</b>
                </div>
                <div class="qr-url" style="margin-top:8px">
                    <a href="/observe/${qr.qr_token}" target="_blank"
                       style="color:var(--accent);font-size:0.72rem;text-decoration:none;">
                        🔗 /observe/${qr.qr_token}
                    </a>
                </div>
                <a href="/qr-codes/${qr.qr_token}/image" download="QR-${qr.qr_token}.png"
                   class="btn btn-ghost" style="margin-top:10px;width:100%;text-align:center;font-size:0.75rem;padding:6px;display:block;text-decoration:none;">
                    ⬇ Download QR PNG
                </a>
            </div>`).join('');
    } catch(e) {
        el.innerHTML = '<div class="empty">Failed to load QR codes.</div>';
    }
}

async function createQR() {
    const token    = document.getElementById('qr-token').value.trim();
    const bus      = document.getElementById('qr-bus').value.trim();
    const route    = document.getElementById('qr-route').value.trim();
    const location = document.getElementById('qr-location').value.trim();
    const msg      = document.getElementById('qr-msg');

    if (!token) { msg.style.color='#f87171'; msg.textContent='Token is required.'; return; }

    const res = await fetch('/qr-codes', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ qr_token:token, bus_number:bus||null, route_id:route||null, location:location||null })
    });
    const data = await res.json();
    if (res.ok) {
        msg.style.color = '#4ade80';
        msg.textContent = `Registered! Scan URL: /observe/${token}`;
        document.getElementById('qr-token').value = '';
        document.getElementById('qr-bus').value = '';
        document.getElementById('qr-route').value = '';
        document.getElementById('qr-location').value = '';
        // Reload QR list so the new code + image appears immediately
        await loadQRCodes();
    } else {
        msg.style.color = '#f87171';
        msg.textContent = '❌ ' + (data.detail || 'Error');
    }
}

// Initial load
loadDashboard();
</script>
</body>
</html>
    """)


# =======================================================================
# Export (for Fabric / Data Factory ingestion)
# =======================================================================

@app.get("/export/observations-csv", tags=["Export"])
def export_observations_csv(
    days: int = Query(7, description="Export last N days"),
    db: Session = Depends(get_db),
):
    """
    Download observations as CSV.
    In production: trigger from a Data Factory pipeline to land
    data in trace_lakehouse/Files/observations/.
    """
    obs_list = crud.get_observations(db, days=days, limit=50000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "route_id", "bus_number", "problem_type", "severity",
        "status", "description", "latitude", "longitude",
        "observed_at", "created_at",
    ])
    for o in obs_list:
        writer.writerow([
            o.id, o.route_id, o.bus_number,
            o.problem_type.value if hasattr(o.problem_type, "value") else o.problem_type,
            o.severity.value if hasattr(o.severity, "value") else o.severity,
            o.status.value if hasattr(o.status, "value") else o.status,
            o.description, o.latitude, o.longitude,
            o.observed_at, o.created_at,
        ])

    output.seek(0)
    filename = f"trace_observations_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
