"""MDP schema definitions for the CAR-T manufacturing scheduling problem.

These Pydantic models define the data contracts for the entire system:
- State: what the agent observes
- Action: what the agent can do
- Reward: how the agent is evaluated
- Config: tunable parameters (never hardcoded)
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SuiteStatus(str, Enum):
    """Operational status of a cleanroom suite."""

    IDLE = "idle"
    IN_USE = "in_use"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"


class BatchPhase(str, Enum):
    """Manufacturing phase within a batch's lifecycle.

    Order matters: each phase follows the previous sequentially.
    A batch cannot skip phases or go backwards.
    """

    ISOLATION = "isolation"
    ACTIVATION = "activation"
    TRANSDUCTION = "transduction"
    EXPANSION = "expansion"
    HARVEST = "harvest"
    FORMULATION = "formulation"
    QC = "qc"


# ---------------------------------------------------------------------------
# State components
# ---------------------------------------------------------------------------

class Suite(BaseModel):
    """A single cleanroom suite and its current operational state."""

    id: str = Field(..., description="Unique suite identifier, e.g. 'SUITE-01'")
    status: SuiteStatus
    current_batch_id: str | None = Field(
        default=None,
        description="Batch currently occupying this suite, if any",
    )
    current_phase: BatchPhase | None = Field(
        default=None,
        description="Manufacturing phase of the current batch",
    )
    days_remaining_estimate: float = Field(
        default=0.0,
        ge=0.0,
        description="Point estimate of days until suite is free",
    )
    days_remaining_variance: float = Field(
        default=0.0,
        ge=0.0,
        description="Variance of the remaining-days estimate",
    )

    @model_validator(mode="after")
    def _validate_occupancy(self) -> Suite:
        """If suite is idle, it should not have a batch or phase."""
        if self.status == SuiteStatus.IDLE:
            if self.current_batch_id is not None:
                raise ValueError("Idle suite must not have a current_batch_id")
            if self.current_phase is not None:
                raise ValueError("Idle suite must not have a current_phase")
        if self.status == SuiteStatus.IN_USE:
            if self.current_batch_id is None:
                raise ValueError("In-use suite must have a current_batch_id")
            if self.current_phase is None:
                raise ValueError("In-use suite must have a current_phase")
        return self


class Patient(BaseModel):
    """A patient in the scheduling queue awaiting manufacturing."""

    patient_id: str = Field(..., description="Unique patient identifier, e.g. 'PT-2401'")
    indication: str = Field(
        ...,
        description="Cancer indication, e.g. 'DLBCL', 'ALL', 'MCL'",
    )
    acuity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Clinical urgency score: 0 = stable, 1 = critical",
    )
    days_waiting: int = Field(
        ...,
        ge=0,
        description="Days since patient entered the queue",
    )
    cell_viability_days_remaining: int = Field(
        ...,
        ge=0,
        description="Days before collected cells are no longer viable",
    )
    scheduled_leukapheresis_date: date | None = Field(
        default=None,
        description="Date leukapheresis is scheduled (None if already completed)",
    )
    cells_collected_date: date | None = Field(
        default=None,
        description="Date cells were actually collected (None if not yet collected)",
    )


class IncomingPatient(BaseModel):
    """A patient in the intake pipeline who has not yet entered the queue."""

    patient_id: str
    estimated_arrival_days: int = Field(
        ...,
        ge=0,
        description="Estimated days until this patient's cells arrive at the facility",
    )
    priority: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Preliminary priority score",
    )


class Inventory(BaseModel):
    """Consumable inventory levels at the facility."""

    media_units: int = Field(..., ge=0)
    viral_vector_doses: int = Field(..., ge=0)
    reagent_kits: int = Field(..., ge=0)


class State(BaseModel):
    """Complete MDP state at a single decision point.

    This is the observation the RL agent receives. Every field must be
    derivable from data sources (Vineti, MES, LIMS, EHR) or the simulator.
    """

    suites: list[Suite] = Field(..., min_length=1, description="All suites at the facility")
    patient_queue: list[Patient] = Field(
        default_factory=list,
        description="Patients awaiting manufacturing, ordered by arrival",
    )
    inventory: Inventory
    incoming_pipeline: list[IncomingPatient] = Field(
        default_factory=list,
        description="Patients expected to arrive in the near future",
    )
    clock: datetime = Field(..., description="Current simulation or real-world time")

    @property
    def idle_suites(self) -> list[Suite]:
        """Suites that are available for a new batch."""
        return [s for s in self.suites if s.status == SuiteStatus.IDLE]

    @property
    def num_idle_suites(self) -> int:
        return len(self.idle_suites)

    @property
    def num_patients_waiting(self) -> int:
        return len(self.patient_queue)

    @property
    def has_actionable_assignment(self) -> bool:
        """True if there is at least one idle suite and one waiting patient."""
        return self.num_idle_suites > 0 and self.num_patients_waiting > 0


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

class AssignAction(BaseModel):
    """Assign a patient to a cleanroom suite."""

    type: Literal["assign"] = "assign"
    patient_id: str
    suite_id: str
    start_time: datetime


class NoOpAction(BaseModel):
    """Do nothing — wait for the next decision point."""

    type: Literal["no_op"] = "no_op"


Action = Annotated[Union[AssignAction, NoOpAction], Field(discriminator="type")]


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------

class RewardWeights(BaseModel):
    """Tunable weights for the reward function.

    These must NEVER be hardcoded — always loaded from config.
    See PROJECT_CONTEXT.md §5 for justification of defaults.
    """

    wait_time: float = Field(
        default=1.0,
        ge=0.0,
        description="Penalty per patient-day of wait (alpha)",
    )
    idle_time: float = Field(
        default=0.2,
        ge=0.0,
        description="Penalty per suite-day idle (beta)",
    )
    batch_failure: float = Field(
        default=50.0,
        ge=0.0,
        description="Penalty per batch failure (gamma_reward)",
    )
    successful_infusion: float = Field(
        default=100.0,
        ge=0.0,
        description="Reward per successful infusion (delta)",
    )
    constraint_violation: float = Field(
        default=1000.0,
        ge=0.0,
        description="Penalty per hard constraint violation (epsilon)",
    )
    valid_assignment: float = Field(
        default=10.0,
        ge=0.0,
        description="Immediate bonus per valid patient-to-suite assignment (zeta)",
    )
    acuity_exponent: float = Field(
        default=2.0,
        ge=1.0,
        description="Exponent for acuity-weighted wait penalty. "
        "At 2.0, a patient with acuity 0.9 generates ~4x the penalty of acuity 0.45",
    )


class RewardComponents(BaseModel):
    """Breakdown of a single reward into its components, for explainability."""

    wait_time_penalty: float = 0.0
    idle_time_penalty: float = 0.0
    batch_failure_penalty: float = 0.0
    infusion_reward: float = 0.0
    constraint_violation_penalty: float = 0.0
    assignment_bonus: float = 0.0


class Reward(BaseModel):
    """Scalar reward with an explainable breakdown."""

    total: float = Field(..., description="Scalar reward signal passed to the agent")
    components: RewardComponents = Field(
        default_factory=RewardComponents,
        description="Per-component breakdown for explainability",
    )

    @classmethod
    def compute(
        cls,
        weights: RewardWeights,
        wait_time_days: float = 0.0,
        idle_time_days: float = 0.0,
        batch_failures: int = 0,
        successful_infusions: int = 0,
        constraint_violations: int = 0,
        valid_assignments: int = 0,
        acuity_weighted_wait_days: float | None = None,
    ) -> Reward:
        """Compute reward from raw metrics and weights.

        R = -alpha * wait - beta * idle - gamma * fail
            + delta * infusion - epsilon * violations + zeta * assignments

        If acuity_weighted_wait_days is provided, it replaces flat wait_time_days.
        """
        effective_wait = (
            acuity_weighted_wait_days if acuity_weighted_wait_days is not None
            else wait_time_days
        )
        components = RewardComponents(
            wait_time_penalty=-weights.wait_time * effective_wait,
            idle_time_penalty=-weights.idle_time * idle_time_days,
            batch_failure_penalty=-weights.batch_failure * batch_failures,
            infusion_reward=weights.successful_infusion * successful_infusions,
            constraint_violation_penalty=-weights.constraint_violation * constraint_violations,
            assignment_bonus=weights.valid_assignment * valid_assignments,
        )
        total = (
            components.wait_time_penalty
            + components.idle_time_penalty
            + components.batch_failure_penalty
            + components.infusion_reward
            + components.constraint_violation_penalty
            + components.assignment_bonus
        )
        return cls(total=total, components=components)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class TransitionDistributions(BaseModel):
    """Stochastic parameters for MDP transitions.

    All distributions are configurable — never hardcode these values.
    Defaults are based on published real-world CAR-T manufacturing data.
    """

    expansion_duration_log_mean: float = Field(
        default=2.6390573296,  # log(14) ≈ 2.639; Novartis Kymriah BLA (2017) reports 14-day median expansion
        description="LogNormal mu for cell expansion duration",
    )
    expansion_duration_log_std: float = Field(
        default=0.25,  # Levine et al. (2017) Cancer Res: observed 10-21 day range → higher variability than 0.15
        gt=0.0,
        description="LogNormal sigma for cell expansion duration",
    )
    qc_pass_probability: float = Field(
        default=0.90,  # FDA BLA reviews: Kymriah ~90%, Yescarta ~92%; range 85-95% depending on product
        ge=0.0,
        le=1.0,
        description="Bernoulli probability that a batch passes QC release",
    )
    patient_arrival_rate: float = Field(
        default=0.3,  # ~2.1 patients/week; realistic for a mid-size CDMO site (ISCT survey data)
        gt=0.0,
        description="Poisson lambda for daily patient arrivals",
    )
    cleaning_duration_days: float = Field(
        default=1.0,
        gt=0.0,
        description="Deterministic suite cleaning duration after batch completion",
    )
    bridging_therapy_fraction: float = Field(
        default=0.65,  # 65% of patients receive bridging therapy; Nastoupil et al. (2020) Blood
        ge=0.0,
        le=1.0,
        description="Fraction of patients receiving bridging therapy while awaiting manufacturing",
    )


class FacilityConfig(BaseModel):
    """Top-level configuration for a manufacturing facility simulation.

    Load from a YAML/JSON config file — never hardcode.
    num_suites=6 represents a mid-size CDMO (typical range 4-12 suites per
    published ISCT/FACT facility surveys).
    """

    num_suites: int = Field(default=6, ge=1, le=50)
    reward_weights: RewardWeights = Field(default_factory=RewardWeights)
    transition_distributions: TransitionDistributions = Field(
        default_factory=TransitionDistributions,
    )
    discount_factor: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="RL discount factor (gamma_rl)",
    )
    decision_interval_hours: float = Field(
        default=8.0,
        gt=0.0,
        description="Hours between decision points (matches shift length)",
    )
    max_episode_days: int = Field(
        default=90,
        gt=0,
        description="Maximum simulation horizon in days",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility (required for compliance)",
    )
