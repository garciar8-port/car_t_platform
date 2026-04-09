"""Audit service with SHA-256 hash chain for 21 CFR Part 11 compliance.

Every audit entry links to the previous entry's hash, forming an
append-only tamper-evident log. Use ``verify_chain`` to detect
any modifications to historical records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditEntry


class AuditService:
    """Manages the immutable audit trail with hash-chain integrity."""

    @staticmethod
    async def log(
        db: AsyncSession,
        *,
        user: str,
        action_type: str,
        subject: str,
        details: str = "",
        justification: str | None = None,
        model_version: str = "v0.4.0-phase4",
    ) -> AuditEntry:
        """Append a new audit entry, chaining its hash to the previous entry."""
        # Get previous hash for chain
        result = await db.execute(
            select(AuditEntry).order_by(desc(AuditEntry.timestamp)).limit(1)
        )
        prev = result.scalar_one_or_none()
        previous_hash = prev.entry_hash if prev else "0" * 64

        entry = AuditEntry(
            id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            user=user,
            action_type=action_type,
            subject=subject,
            details=details,
            justification=justification,
            model_version=model_version,
            signature_status="signed",
            previous_hash=previous_hash,
        )
        entry.entry_hash = entry.compute_hash()
        db.add(entry)
        await db.commit()
        return entry

    @staticmethod
    async def get_trail(db: AsyncSession, limit: int = 100) -> list[AuditEntry]:
        """Return the most recent audit entries, newest first."""
        result = await db.execute(
            select(AuditEntry).order_by(desc(AuditEntry.timestamp)).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def verify_chain(db: AsyncSession) -> bool:
        """Verify the hash chain integrity -- detects any tampering."""
        result = await db.execute(
            select(AuditEntry).order_by(AuditEntry.timestamp)
        )
        entries = list(result.scalars().all())
        for i, entry in enumerate(entries):
            expected_prev = entries[i - 1].entry_hash if i > 0 else "0" * 64
            if entry.previous_hash != expected_prev:
                return False
            if entry.entry_hash != entry.compute_hash():
                return False
        return True
