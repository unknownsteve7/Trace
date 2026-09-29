from typing import Optional, List
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

import models
import schemas


# ---------------------------------------------------------------------
# QR Codes
# ---------------------------------------------------------------------

def create_qr_code(db: Session, qr: schemas.QRCodeCreate) -> models.QRCode:
    db_qr = models.QRCode(
        qr_token=qr.qr_token,
        bus_number=qr.bus_number,
        route_id=qr.route_id,
        location=qr.location,
    )
    db.add(db_qr)
    db.commit()
    db.refresh(db_qr)
    return db_qr


def get_qr_code_by_token(db: Session, qr_token: str) -> Optional[models.QRCode]:
    return db.query(models.QRCode).filter(models.QRCode.qr_token == qr_token).first()


# ---------------------------------------------------------------------
# Observations
# ---------------------------------------------------------------------

def check_recent_duplicate(
    db: Session,
    qr_code_id: int,
    anonymous_identifier: str,
    window_minutes: int = 60,
) -> Optional[models.Observation]:
    """
    Prevents spam: same identifier cannot submit more than once
    per QR code within the time window.
    Multiple different identifiers CAN report the same QR code —
    that's intentional (signal strength from multiple observers).
    """
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    return (
        db.query(models.Observation)
        .filter(
            models.Observation.qr_code_id == qr_code_id,
            models.Observation.anonymous_identifier == anonymous_identifier,
            models.Observation.created_at >= cutoff,
        )
        .first()
    )


def create_observation(
    db: Session, obs: schemas.ObservationCreate, qr_code: models.QRCode
) -> models.Observation:
    db_obs = models.Observation(
        qr_code_id=qr_code.id,
        bus_number=qr_code.bus_number,
        route_id=qr_code.route_id,
        problem_type=obs.problem_type,
        severity=obs.severity,
        description=obs.description,
        observed_at=obs.observed_at,
        latitude=obs.latitude,
        longitude=obs.longitude,
        anonymous_identifier=obs.anonymous_identifier,
        status=models.ObservationStatus.NEW,
    )
    db.add(db_obs)
    db.commit()
    db.refresh(db_obs)
    return db_obs


def get_observation(db: Session, observation_id: int) -> Optional[models.Observation]:
    return db.query(models.Observation).filter(models.Observation.id == observation_id).first()


def get_observations(
    db: Session,
    problem_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    route_id: Optional[str] = None,
    bus_number: Optional[str] = None,
    days: Optional[int] = None,
    skip: int = 0,
    limit: int = 200,
) -> List[models.Observation]:
    query = db.query(models.Observation)

    if problem_type:
        query = query.filter(models.Observation.problem_type == problem_type)
    if severity:
        query = query.filter(models.Observation.severity == severity)
    if status:
        query = query.filter(models.Observation.status == status)
    if route_id:
        query = query.filter(models.Observation.route_id == route_id)
    if bus_number:
        query = query.filter(models.Observation.bus_number == bus_number)
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(models.Observation.created_at >= cutoff)

    return query.order_by(models.Observation.created_at.desc()).offset(skip).limit(limit).all()


def update_observation_status(
    db: Session, observation_id: int, new_status: models.ObservationStatus
) -> Optional[models.Observation]:
    db_obs = get_observation(db, observation_id)
    if db_obs is None:
        return None
    db_obs.status = new_status
    db.commit()
    db.refresh(db_obs)
    return db_obs


# ---------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------

def get_observations_by_route(
    db: Session, days: int = 30
) -> list:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(
            models.Observation.route_id,
            models.Observation.problem_type,
            models.Observation.severity,
            func.count(models.Observation.id).label("count"),
        )
        .filter(models.Observation.created_at >= cutoff)
        .filter(models.Observation.route_id.isnot(None))
        .group_by(
            models.Observation.route_id,
            models.Observation.problem_type,
            models.Observation.severity,
        )
        .order_by(func.count(models.Observation.id).desc())
        .limit(50)
        .all()
    )


def get_summary_by_problem_type(db: Session, days: int = 30) -> list:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(
            models.Observation.problem_type,
            models.Observation.severity,
            func.count(models.Observation.id).label("count"),
        )
        .filter(models.Observation.created_at >= cutoff)
        .group_by(models.Observation.problem_type, models.Observation.severity)
        .order_by(func.count(models.Observation.id).desc())
        .all()
    )


# ---------------------------------------------------------------------
# Admin summary
# ---------------------------------------------------------------------

def get_summary(db: Session) -> dict:
    total         = db.query(models.Observation).count()
    new_count     = db.query(models.Observation).filter(models.Observation.status == models.ObservationStatus.NEW).count()
    reviewed_count= db.query(models.Observation).filter(models.Observation.status == models.ObservationStatus.REVIEWED).count()
    resolved_count= db.query(models.Observation).filter(models.Observation.status == models.ObservationStatus.RESOLVED).count()
    high_count    = db.query(models.Observation).filter(models.Observation.severity == models.Severity.HIGH).count()
    critical_count= db.query(models.Observation).filter(models.Observation.severity == models.Severity.CRITICAL).count()

    top_problem_rows = (
        db.query(
            models.Observation.problem_type,
            func.count(models.Observation.id).label("count"),
        )
        .group_by(models.Observation.problem_type)
        .order_by(func.count(models.Observation.id).desc())
        .limit(5)
        .all()
    )

    top_problem_types = [
        {"problem_type": row[0].value if hasattr(row[0], "value") else row[0], "count": row[1]}
        for row in top_problem_rows
    ]

    return {
        "total_observations":    total,
        "new_observations":      new_count,
        "reviewed_observations": reviewed_count,
        "resolved_observations": resolved_count,
        "high_priority":         high_count,
        "critical_priority":     critical_count,
        "top_problem_types":     top_problem_types,
    }
