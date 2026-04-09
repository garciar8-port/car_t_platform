"""SQLAlchemy ORM models for BioFlow Scheduler API.

All models use SQLAlchemy 2.0 mapped_column style.
AuditEntry implements a SHA-256 hash chain for 21 CFR Part 11 tamper evidence.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class AuditEntry(Base):
    """Immutable, append-only audit trail with hash-chain tamper evidence."""

    __tablename__ = "audit_entries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, default="")
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50))
    signature_status: Mapped[str] = mapped_column(String(20), default="signed")
    previous_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    def compute_hash(self) -> str:
        """Create SHA-256 of key fields for tamper-evidence chain."""
        payload = (
            f"{self.timestamp.isoformat() if self.timestamp else ''}"
            f"{self.user}"
            f"{self.action_type}"
            f"{self.subject}"
            f"{self.details or ''}"
            f"{self.previous_hash or ''}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class User(Base):
    """Application user — coordinator, director, QA reviewer, or admin."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    site: Mapped[str] = mapped_column(String(100), default="Rockville Site A")
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SchedulingDecision(Base):
    """Records each scheduling recommendation and the coordinator's decision."""

    __tablename__ = "scheduling_decisions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    patient_id: Mapped[str] = mapped_column(String(50), nullable=False)
    recommended_suite: Mapped[str | None] = mapped_column(String(50))
    recommended_action: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[float | None] = mapped_column(Float)
    shap_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    decision: Mapped[str | None] = mapped_column(String(20))
    override_suite: Mapped[str | None] = mapped_column(String(50), nullable=True)
    override_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(50))


class HandoffReport(Base):
    """Shift handoff report — captures notes, checklist, and e-signature."""

    __tablename__ = "handoff_reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    shift: Mapped[str] = mapped_column(String(20), nullable=False)
    site: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    checked_items: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    signed: Mapped[bool] = mapped_column(Boolean, default=False)
    signature_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
