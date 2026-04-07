"""Adversarial stress scenarios for CAR-T manufacturing simulation.

Configurable scenario objects that modify simulator behavior at specific
time points to test agent robustness under realistic failure modes:
contamination events, patient surges, equipment failures, supply shortages.
"""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, Field


class StressScenario(BaseModel):
    """Base class for all stress scenarios."""

    name: str
    description: str


class QCFailureWave(StressScenario):
    """Simulates a contamination event (e.g., mycoplasma in shared reagent lot).

    During the event window, QC failure rate spikes dramatically.
    """

    type: Literal["qc_failure_wave"] = "qc_failure_wave"
    start_day: int = Field(..., ge=0)
    duration_days: int = Field(..., gt=0)
    failure_rate: float = Field(
        ..., ge=0, le=1,
        description="QC failure rate during the event (e.g., 0.50 = 50% failure)",
    )


class PatientSurge(StressScenario):
    """Simulates a clinical trial enrollment spike or seasonal demand.

    Patient arrival rate is multiplied during the event window.
    """

    type: Literal["patient_surge"] = "patient_surge"
    start_day: int = Field(..., ge=0)
    duration_days: int = Field(..., gt=0)
    arrival_rate_multiplier: float = Field(
        ..., gt=1.0,
        description="Multiplier for patient arrival rate (e.g., 3.0 = 3x normal)",
    )


class EquipmentFailure(StressScenario):
    """Simulates isolator failure, HVAC breakdown, or decontamination event.

    A suite goes to maintenance for a specified duration.
    """

    type: Literal["equipment_failure"] = "equipment_failure"
    day: int = Field(..., ge=0, description="Day when the failure occurs")
    suite_index: int = Field(
        default=0, ge=0,
        description="Index of the suite that fails (0-based)",
    )
    downtime_days: int = Field(..., gt=0)


class SupplyShortage(StressScenario):
    """Simulates a viral vector manufacturing delay or supply chain disruption.

    Inventory drops to a specified level at a given day, with no resupply.
    """

    type: Literal["supply_shortage"] = "supply_shortage"
    start_day: int = Field(..., ge=0)
    resource: Literal["media", "viral_vector", "reagent"]
    remaining_units: int = Field(
        ..., ge=0,
        description="Inventory drops to this level",
    )


ScenarioType = Union[QCFailureWave, PatientSurge, EquipmentFailure, SupplyShortage]


# ---------------------------------------------------------------------------
# Standard stress test battery
# ---------------------------------------------------------------------------

STANDARD_SCENARIOS: list[ScenarioType] = [
    QCFailureWave(
        name="QC contamination event",
        description="Mycoplasma detected in shared reagent lot — QC failure rate "
        "spikes to 50% for 10 days starting day 30",
        start_day=30,
        duration_days=10,
        failure_rate=0.50,
    ),
    PatientSurge(
        name="Clinical trial enrollment spike",
        description="Phase III trial opens enrollment — 3x patient arrivals "
        "for 14 days starting day 20",
        start_day=20,
        duration_days=14,
        arrival_rate_multiplier=3.0,
    ),
    EquipmentFailure(
        name="Isolator failure",
        description="Suite 1 isolator HVAC failure — 7 days of maintenance "
        "starting day 25",
        day=25,
        suite_index=0,
        downtime_days=7,
    ),
    SupplyShortage(
        name="Viral vector supply disruption",
        description="Vector manufacturing delay at CDMO — viral vector inventory "
        "drops to 2 doses at day 15, no resupply",
        start_day=15,
        resource="viral_vector",
        remaining_units=2,
    ),
]
