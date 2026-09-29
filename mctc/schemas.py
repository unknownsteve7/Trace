"""
schemas.py
----------
Pydantic models used for request validation and response shaping.

These are kept separate from the SQLAlchemy models (models.py) on
purpose: schemas.py defines what the API accepts/returns, models.py
defines how data is stored.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from models import ProblemType, Severity, ObservationStatus


# ---------------------------------------------------------------------
# QR Code schemas
# ---------------------------------------------------------------------

class QRCodeCreate(BaseModel):
    qr_token: str = Field(..., min_length=1, max_length=50)
    bus_number: Optional[str] = Field(None, max_length=50)
    route_id: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)


class QRCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    qr_token: str
    bus_number: Optional[str]
    route_id: Optional[str]
    location: Optional[str]
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------------------
# Observation schemas
# ---------------------------------------------------------------------

class ObservationCreate(BaseModel):
    qr_token: str = Field(..., min_length=1, max_length=50)
    problem_type: ProblemType
    severity: Severity
    description: Optional[str] = Field(None, max_length=1000)
    observed_at: datetime
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    anonymous_identifier: str = Field(..., min_length=1, max_length=100)


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    qr_code_id: int
    bus_number: Optional[str]
    route_id: Optional[str]
    problem_type: ProblemType
    severity: Severity
    description: Optional[str]
    observed_at: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    status: ObservationStatus
    created_at: datetime


class ObservationSubmitResponse(BaseModel):
    message: str
    observation_id: int


class ObservationStatusUpdate(BaseModel):
    status: ObservationStatus


# ---------------------------------------------------------------------
# /observe/{qr_token} response
# ---------------------------------------------------------------------

class ObserveFormResponse(BaseModel):
    message: str
    qr_token: str
    bus_number: Optional[str]
    route_id: Optional[str]
    location: Optional[str]
    active: bool
    problem_types: List[str]
    severities: List[str]


# ---------------------------------------------------------------------
# Admin summary
# ---------------------------------------------------------------------

class ProblemTypeCount(BaseModel):
    problem_type: str
    count: int


class AdminSummary(BaseModel):
    total_observations: int
    new_observations: int
    reviewed_observations: int
    resolved_observations: int
    high_priority: int
    critical_priority: int
    top_problem_types: List[ProblemTypeCount]
