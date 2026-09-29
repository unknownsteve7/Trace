"""
models.py
---------
SQLAlchemy ORM models for the MCTC Ground-Level Operational
Observation System.

Two tables:

1. QRCode        -> represents a physical QR code attached to a bus
                     or a fixed operational location (e.g. a bus stop).
2. Observation   -> a single ground-level operational observation
                     submitted by scanning a QR code.

Relationship:
    One QRCode  ->  Many Observations
"""

import enum
from datetime import datetime

# pyrefly: ignore [missing-import]
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Text,
    Float,
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------

class ProblemType(str, enum.Enum):
    """
    Ground-level operational problem categories.
    Each one is meant to later be cross-checked against real
    operational data (GPS, GTFS, ridership, weather, traffic, fuel,
    maintenance) by the analytics layer.
    """
    BUS_DELAY          = "BUS_DELAY"
    BUS_NOT_ARRIVED    = "BUS_NOT_ARRIVED"
    BUS_BUNCHING       = "BUS_BUNCHING"
    LONG_SERVICE_GAP   = "LONG_SERVICE_GAP"
    OVER_CROWDING      = "OVER_CROWDING"
    UNDER_UTILIZATION  = "UNDER_UTILIZATION"
    VEHICLE_CONDITION  = "VEHICLE_CONDITION"
    VEHICLE_BREAKDOWN  = "VEHICLE_BREAKDOWN"
    MAINTENANCE_ISSUE  = "MAINTENANCE_ISSUE"
    FUEL_CONSUMPTION   = "FUEL_CONSUMPTION"
    SAFETY_ISSUE       = "SAFETY_ISSUE"
    ROUTE_ISSUE        = "ROUTE_ISSUE"
    STOP_INFRASTRUCTURE = "STOP_INFRASTRUCTURE"
    WEATHER_DISRUPTION = "WEATHER_DISRUPTION"
    TRAFFIC_DISRUPTION = "TRAFFIC_DISRUPTION"
    OTHER              = "OTHER"


class Severity(str, enum.Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class ObservationStatus(str, enum.Enum):
    NEW      = "NEW"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"


# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

class QRCode(Base):
    """
    Represents a single physical QR code tied to a bus/route/location.
    The QR image is generated client-side from the token; only the
    token is stored here.
    """
    __tablename__ = "qr_codes"

    id         = Column(Integer, primary_key=True, index=True)
    qr_token   = Column(String, unique=True, index=True, nullable=False)
    bus_number = Column(String, nullable=True)
    route_id   = Column(String, nullable=True)
    location   = Column(String, nullable=True)
    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    observations = relationship(
        "Observation",
        back_populates="qr_code",
        cascade="all, delete-orphan",
    )


class Observation(Base):
    """
    A single ground-level operational observation submitted by
    scanning a QR code.

    CHANGE from v0.1: Removed the UniqueConstraint on
    (qr_code_id, anonymous_identifier). Multiple field observers
    should be able to report the same issue on the same bus.
    Spam is now controlled at the application level via a
    time-window check (60 minutes per identifier per QR code).
    """
    __tablename__ = "observations"

    id           = Column(Integer, primary_key=True, index=True)
    qr_code_id   = Column(Integer, ForeignKey("qr_codes.id"), nullable=False)

    # Denormalized at time of submission (QR assignment can change)
    bus_number   = Column(String, nullable=True)
    route_id     = Column(String, nullable=True)

    problem_type = Column(SAEnum(ProblemType), nullable=False)
    severity     = Column(SAEnum(Severity), nullable=False)
    description  = Column(Text, nullable=True)
    observed_at  = Column(DateTime, nullable=False)

    latitude     = Column(Float, nullable=True)
    longitude    = Column(Float, nullable=True)

    # Used only for time-window spam control, not identity tracking.
    anonymous_identifier = Column(String, nullable=False)

    status     = Column(
        SAEnum(ObservationStatus),
        default=ObservationStatus.NEW,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    qr_code = relationship("QRCode", back_populates="observations")
