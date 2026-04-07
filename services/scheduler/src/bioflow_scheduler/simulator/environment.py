"""Core discrete-event simulation of a CAR-T manufacturing facility.

Uses SimPy to model cleanroom suites processing patient batches through
seven sequential manufacturing phases with stochastic durations and QC outcomes.

The simulator is the "digital twin" the RL agent trains against. It can also
be used standalone for what-if analysis and baseline benchmarking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Literal

import numpy as np
import simpy
from pydantic import BaseModel, Field

from bioflow_scheduler.mdp.schemas import (
    AssignAction,
    BatchPhase,
    FacilityConfig,
    Inventory,
    NoOpAction,
    Patient,
    Reward,
    State,
    Suite,
    SuiteStatus,
)
from bioflow_scheduler.simulator.scenarios import (
    EquipmentFailure,
    PatientSurge,
    QCFailureWave,
    ScenarioType,
    SupplyShortage,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOURS_PER_DAY = 24.0

# Indications used for random patient generation
INDICATIONS = ["DLBCL", "ALL", "MCL", "FL", "CLL"]

# Expected total processing days by indication (for SPT heuristic and patient gen)
INDICATION_MEAN_DAYS: dict[str, float] = {
    "DLBCL": 21.0,
    "ALL": 18.0,
    "MCL": 23.0,
    "FL": 20.0,
    "CLL": 22.0,
}


# ---------------------------------------------------------------------------
# Phase duration configuration
# ---------------------------------------------------------------------------

class DistributionType(str, Enum):
    DETERMINISTIC = "deterministic"
    LOGNORMAL = "lognormal"


class PhaseDurationConfig(BaseModel):
    """Duration parameters for a single manufacturing phase."""

    mean_days: float = Field(..., gt=0)
    std_days: float = Field(default=0.0, ge=0)
    distribution: DistributionType = DistributionType.DETERMINISTIC


# Defaults based on published CAR-T manufacturing timelines.
# EXPANSION uses lognormal (the primary stochastic phase).
# Other phases are deterministic in MVP — the stochasticity in QC
# is in the pass/fail outcome, not the duration.
DEFAULT_PHASE_DURATIONS: dict[BatchPhase, PhaseDurationConfig] = {
    BatchPhase.ISOLATION: PhaseDurationConfig(mean_days=1.0),
    BatchPhase.ACTIVATION: PhaseDurationConfig(mean_days=2.0),
    BatchPhase.TRANSDUCTION: PhaseDurationConfig(mean_days=1.0),
    BatchPhase.EXPANSION: PhaseDurationConfig(
        mean_days=14.0,
        std_days=2.0,
        distribution=DistributionType.LOGNORMAL,
    ),
    BatchPhase.HARVEST: PhaseDurationConfig(mean_days=1.0),
    BatchPhase.FORMULATION: PhaseDurationConfig(mean_days=1.0),
    BatchPhase.QC: PhaseDurationConfig(mean_days=3.0),
}

# Ordered list of phases for sequential iteration
PHASE_ORDER: list[BatchPhase] = list(BatchPhase)


# ---------------------------------------------------------------------------
# Internal tracking
# ---------------------------------------------------------------------------

@dataclass
class BatchTracker:
    """Internal state for a running batch (not exposed via MDP schemas)."""

    batch_id: str
    patient_id: str
    suite_id: str
    start_time: float  # SimPy time (hours)
    current_phase: BatchPhase = BatchPhase.ISOLATION
    qc_passed: bool | None = None
    completed: bool = False
    failed: bool = False


@dataclass
class IntervalMetrics:
    """Metrics accumulated during a single decision interval."""

    wait_time_days: float = 0.0
    acuity_weighted_wait_days: float = 0.0
    idle_time_days: float = 0.0
    successful_infusions: int = 0
    batch_failures: int = 0
    constraint_violations: int = 0
    valid_assignments: int = 0


# ---------------------------------------------------------------------------
# Main simulator
# ---------------------------------------------------------------------------

class ManufacturingSimulator:
    """Discrete-event simulation of a CAR-T manufacturing facility.

    Usage::

        sim = ManufacturingSimulator(FacilityConfig(seed=42))
        state = sim.reset()
        while True:
            action = policy.select_action(state)
            state, reward, done, info = sim.step(action)
            if done:
                break
    """

    def __init__(
        self,
        config: FacilityConfig | None = None,
        phase_durations: dict[BatchPhase, PhaseDurationConfig] | None = None,
        scenarios: list[ScenarioType] | None = None,
    ) -> None:
        self.config = config or FacilityConfig()
        self.phase_durations = phase_durations or dict(DEFAULT_PHASE_DURATIONS)
        self.scenarios = scenarios or []

        # These are initialized in reset()
        self._simpy_env: simpy.Environment | None = None
        self._rng: np.random.Generator | None = None
        self._suite_states: dict[str, _SuiteInternal] = {}
        self._patient_queue: list[Patient] = []
        self._incoming_pipeline: list[Patient] = []
        self._batches: dict[str, BatchTracker] = {}
        self._inventory: Inventory | None = None
        self._batch_counter: int = 0
        self._patient_counter: int = 0
        self._interval_metrics: IntervalMetrics = IntervalMetrics()
        self._episode_step: int = 0
        self._epoch: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> State:
        """Reset the simulation to its initial state."""
        seed = self.config.seed if self.config.seed is not None else 0
        self._rng = np.random.default_rng(seed)
        self._simpy_env = simpy.Environment()
        self._batch_counter = 0
        self._patient_counter = 0
        self._episode_step = 0
        self._batches = {}
        self._interval_metrics = IntervalMetrics()

        # Initialize suites
        self._suite_states = {}
        for i in range(self.config.num_suites):
            suite_id = f"SUITE-{i + 1:02d}"
            self._suite_states[suite_id] = _SuiteInternal(suite_id=suite_id)

        # Initialize inventory
        self._inventory = Inventory(
            media_units=self.config.num_suites * 10,
            viral_vector_doses=self.config.num_suites * 5,
            reagent_kits=self.config.num_suites * 8,
        )

        # Seed the patient queue with a few initial patients
        initial_patients = self._rng.poisson(self.config.num_suites)
        initial_patients = max(initial_patients, 1)  # At least one patient
        self._patient_queue = []
        for _ in range(initial_patients):
            self._patient_queue.append(self._generate_random_patient())

        self._incoming_pipeline = []

        # Start background processes
        self._simpy_env.process(self._patient_arrival_process())

        # Start scenario processes
        for scenario in self.scenarios:
            if isinstance(scenario, EquipmentFailure):
                self._simpy_env.process(self._equipment_failure_process(scenario))

        return self._build_state()

    def step(
        self, action: AssignAction | NoOpAction
    ) -> tuple[State, Reward, bool, dict]:
        """Execute an action and advance to the next decision point.

        Returns:
            (state, reward, done, info) tuple.
        """
        assert self._simpy_env is not None, "Call reset() before step()"
        assert self._rng is not None

        self._interval_metrics = IntervalMetrics()

        # Validate and apply action
        violations = self._apply_action(action)
        self._interval_metrics.constraint_violations += violations

        # Record pre-advance state for idle/wait tracking
        num_waiting_before = len(self._patient_queue)
        idle_suites_before = sum(
            1 for s in self._suite_states.values() if s.status == SuiteStatus.IDLE
        )

        # Apply supply shortage scenarios
        self._apply_supply_shortages()

        # Advance simulation to next decision point
        interval_hours = self.config.decision_interval_hours
        target_time = self._simpy_env.now + interval_hours
        self._simpy_env.run(until=target_time)

        # Compute interval metrics
        interval_days = interval_hours / HOURS_PER_DAY

        # Wait time: acuity-weighted — sicker patients generate more penalty
        acuity_exp = self.config.reward_weights.acuity_exponent
        acuity_weighted_wait = sum(
            (p.acuity_score ** acuity_exp) * interval_days
            for p in self._patient_queue[:num_waiting_before]
        )
        self._interval_metrics.wait_time_days += num_waiting_before * interval_days
        self._interval_metrics.acuity_weighted_wait_days += acuity_weighted_wait

        # Idle time: each idle suite accumulates idle time during the interval
        self._interval_metrics.idle_time_days += idle_suites_before * interval_days

        # Age patients in queue
        for patient in self._patient_queue:
            # We create new Patient objects since they're immutable Pydantic models
            pass  # days_waiting is tracked via the clock difference

        # Compute reward
        reward = Reward.compute(
            weights=self.config.reward_weights,
            wait_time_days=self._interval_metrics.wait_time_days,
            idle_time_days=self._interval_metrics.idle_time_days,
            batch_failures=self._interval_metrics.batch_failures,
            successful_infusions=self._interval_metrics.successful_infusions,
            constraint_violations=self._interval_metrics.constraint_violations,
            valid_assignments=self._interval_metrics.valid_assignments,
            acuity_weighted_wait_days=self._interval_metrics.acuity_weighted_wait_days,
        )

        self._episode_step += 1
        done = self._simpy_env.now >= self.config.max_episode_days * HOURS_PER_DAY

        state = self._build_state()
        info = {
            "episode_step": self._episode_step,
            "sim_time_hours": self._simpy_env.now,
            "sim_time_days": self._simpy_env.now / HOURS_PER_DAY,
            "reward_components": reward.components.model_dump(),
            "active_batches": len([b for b in self._batches.values() if not b.completed]),
            "total_infusions": sum(
                1 for b in self._batches.values() if b.completed and not b.failed
            ),
            "total_failures": sum(1 for b in self._batches.values() if b.failed),
        }

        return state, reward, done, info

    # ------------------------------------------------------------------
    # State construction
    # ------------------------------------------------------------------

    def _build_state(self) -> State:
        """Snapshot current simulation into a State object."""
        assert self._simpy_env is not None
        assert self._inventory is not None

        suites = []
        for sid in sorted(self._suite_states.keys()):
            s = self._suite_states[sid]
            days_remaining = 0.0
            variance = 0.0
            if s.status == SuiteStatus.IN_USE and s.batch_id is not None:
                batch = self._batches.get(s.batch_id)
                if batch is not None:
                    days_remaining = self._estimate_days_remaining(batch)
                    variance = self._estimate_variance(batch)
            elif s.status == SuiteStatus.CLEANING:
                days_remaining = s.cleaning_remaining_hours / HOURS_PER_DAY

            suites.append(
                Suite(
                    id=sid,
                    status=s.status,
                    current_batch_id=s.batch_id if s.status == SuiteStatus.IN_USE else None,
                    current_phase=s.phase if s.status == SuiteStatus.IN_USE else None,
                    days_remaining_estimate=max(0.0, days_remaining),
                    days_remaining_variance=max(0.0, variance),
                )
            )

        clock = self._epoch + timedelta(hours=self._simpy_env.now)

        # Update days_waiting based on sim clock
        updated_queue = []
        for p in self._patient_queue:
            days_in_sim = self._simpy_env.now / HOURS_PER_DAY
            updated_queue.append(
                Patient(
                    patient_id=p.patient_id,
                    indication=p.indication,
                    acuity_score=p.acuity_score,
                    days_waiting=int(days_in_sim) + p.days_waiting,
                    cell_viability_days_remaining=max(
                        0, p.cell_viability_days_remaining - int(days_in_sim)
                    ),
                    scheduled_leukapheresis_date=p.scheduled_leukapheresis_date,
                    cells_collected_date=p.cells_collected_date,
                )
            )

        return State(
            suites=suites,
            patient_queue=updated_queue,
            inventory=self._inventory,
            incoming_pipeline=[],
            clock=clock,
        )

    # ------------------------------------------------------------------
    # Action handling
    # ------------------------------------------------------------------

    def _apply_action(self, action: AssignAction | NoOpAction) -> int:
        """Apply action to the simulation. Returns number of constraint violations."""
        if isinstance(action, NoOpAction):
            return 0

        assert isinstance(action, AssignAction)
        violations = 0

        # Validate patient exists in queue
        patient = None
        patient_idx = None
        for i, p in enumerate(self._patient_queue):
            if p.patient_id == action.patient_id:
                patient = p
                patient_idx = i
                break

        if patient is None:
            violations += 1
            return violations

        # Validate suite exists and is idle
        suite_state = self._suite_states.get(action.suite_id)
        if suite_state is None or suite_state.status != SuiteStatus.IDLE:
            violations += 1
            return violations

        # Check inventory
        assert self._inventory is not None
        if (
            self._inventory.media_units < 1
            or self._inventory.viral_vector_doses < 1
            or self._inventory.reagent_kits < 1
        ):
            violations += 1
            return violations

        # Apply: remove patient, consume inventory, start batch
        self._patient_queue.pop(patient_idx)
        self._inventory = Inventory(
            media_units=self._inventory.media_units - 1,
            viral_vector_doses=self._inventory.viral_vector_doses - 1,
            reagent_kits=self._inventory.reagent_kits - 1,
        )

        self._batch_counter += 1
        batch_id = f"B-{self._batch_counter:04d}"

        batch = BatchTracker(
            batch_id=batch_id,
            patient_id=action.patient_id,
            suite_id=action.suite_id,
            start_time=self._simpy_env.now,  # type: ignore[union-attr]
        )
        self._batches[batch_id] = batch

        # Update suite state
        suite_state.status = SuiteStatus.IN_USE
        suite_state.batch_id = batch_id
        suite_state.phase = BatchPhase.ISOLATION

        # Start batch process
        self._simpy_env.process(self._run_batch(batch))  # type: ignore[union-attr]

        self._interval_metrics.valid_assignments += 1
        return 0

    # ------------------------------------------------------------------
    # SimPy processes
    # ------------------------------------------------------------------

    def _run_batch(self, batch: BatchTracker):  # type: ignore[return]
        """SimPy process: run a batch through all 7 phases."""  # noqa: D401
        assert self._simpy_env is not None
        assert self._rng is not None

        suite = self._suite_states[batch.suite_id]

        for phase in PHASE_ORDER:
            batch.current_phase = phase
            suite.phase = phase

            duration_hours = self._sample_phase_duration(phase) * HOURS_PER_DAY
            yield self._simpy_env.timeout(duration_hours)

            # QC phase: check pass/fail (scenario-aware)
            if phase == BatchPhase.QC:
                passed = self._rng.random() < self._get_qc_pass_probability()
                batch.qc_passed = passed
                if not passed:
                    batch.failed = True
                    batch.completed = True
                    self._interval_metrics.batch_failures += 1
                    # Suite goes to cleaning
                    yield from self._clean_suite(suite)
                    return

        # Batch succeeded
        batch.completed = True
        self._interval_metrics.successful_infusions += 1

        # Suite goes to cleaning
        yield from self._clean_suite(suite)

    def _clean_suite(self, suite: _SuiteInternal):  # type: ignore[return]
        """SimPy process: clean the suite after batch completion."""  # noqa: D401
        assert self._simpy_env is not None

        cleaning_hours = self.config.transition_distributions.cleaning_duration_days * HOURS_PER_DAY
        suite.status = SuiteStatus.CLEANING
        suite.batch_id = None
        suite.phase = None
        suite.cleaning_remaining_hours = cleaning_hours

        yield self._simpy_env.timeout(cleaning_hours)

        suite.status = SuiteStatus.IDLE
        suite.cleaning_remaining_hours = 0.0

    def _patient_arrival_process(self):  # type: ignore[return]
        """SimPy process: generate patient arrivals via Poisson process."""  # noqa: D401
        assert self._simpy_env is not None
        assert self._rng is not None

        # Inter-arrival time is exponential with mean = 1/rate (in days)
        while True:
            rate = self._get_arrival_rate()  # scenario-aware
            inter_arrival_days = self._rng.exponential(1.0 / rate)
            inter_arrival_hours = inter_arrival_days * HOURS_PER_DAY
            yield self._simpy_env.timeout(inter_arrival_hours)

            patient = self._generate_random_patient()
            self._patient_queue.append(patient)

    def _equipment_failure_process(self, scenario: EquipmentFailure):  # type: ignore[return]
        """SimPy process: simulate equipment failure at a scheduled time."""  # noqa: D401
        assert self._simpy_env is not None

        # Wait until the failure day
        yield self._simpy_env.timeout(scenario.day * HOURS_PER_DAY)

        # Find the target suite
        suite_ids = sorted(self._suite_states.keys())
        if scenario.suite_index >= len(suite_ids):
            return
        suite_id = suite_ids[scenario.suite_index]
        suite = self._suite_states[suite_id]

        # Put suite into maintenance
        suite.status = SuiteStatus.MAINTENANCE
        suite.batch_id = None
        suite.phase = None

        # Wait for repair
        yield self._simpy_env.timeout(scenario.downtime_days * HOURS_PER_DAY)

        # Restore suite
        suite.status = SuiteStatus.IDLE

    # ------------------------------------------------------------------
    # Stochastic sampling
    # ------------------------------------------------------------------

    def _sample_phase_duration(self, phase: BatchPhase) -> float:
        """Sample duration in days for a manufacturing phase."""
        assert self._rng is not None

        cfg = self.phase_durations[phase]

        if cfg.distribution == DistributionType.DETERMINISTIC:
            return cfg.mean_days

        if cfg.distribution == DistributionType.LOGNORMAL:
            # Use the config's log-space parameters for expansion
            if phase == BatchPhase.EXPANSION:
                td = self.config.transition_distributions
                return float(
                    self._rng.lognormal(
                        td.expansion_duration_log_mean,
                        td.expansion_duration_log_std,
                    )
                )
            # Generic lognormal for other phases (if ever configured)
            mu = np.log(cfg.mean_days)
            sigma = cfg.std_days / cfg.mean_days  # approximate
            return float(self._rng.lognormal(mu, max(sigma, 0.01)))

        return cfg.mean_days  # fallback

    def _generate_random_patient(self) -> Patient:
        """Generate a patient with randomized attributes."""
        assert self._rng is not None

        self._patient_counter += 1
        patient_id = f"PT-{self._patient_counter:04d}"
        indication = self._rng.choice(INDICATIONS)
        acuity = float(np.clip(self._rng.beta(2, 5), 0.0, 1.0))

        return Patient(
            patient_id=patient_id,
            indication=str(indication),
            acuity_score=round(acuity, 3),
            days_waiting=0,
            cell_viability_days_remaining=int(self._rng.integers(14, 30)),
        )

    # ------------------------------------------------------------------
    # Scenario helpers
    # ------------------------------------------------------------------

    def _current_day(self) -> float:
        """Current simulation day."""
        assert self._simpy_env is not None
        return self._simpy_env.now / HOURS_PER_DAY

    def _get_qc_pass_probability(self) -> float:
        """QC pass probability, accounting for any active QCFailureWave."""
        day = self._current_day()
        for s in self.scenarios:
            if isinstance(s, QCFailureWave):
                if s.start_day <= day < s.start_day + s.duration_days:
                    return 1.0 - s.failure_rate
        return self.config.transition_distributions.qc_pass_probability

    def _get_arrival_rate(self) -> float:
        """Patient arrival rate, accounting for any active PatientSurge."""
        day = self._current_day()
        rate = self.config.transition_distributions.patient_arrival_rate
        for s in self.scenarios:
            if isinstance(s, PatientSurge):
                if s.start_day <= day < s.start_day + s.duration_days:
                    rate *= s.arrival_rate_multiplier
        return rate

    def _apply_supply_shortages(self) -> None:
        """Apply any supply shortage scenarios that have triggered."""
        assert self._inventory is not None
        day = self._current_day()
        for s in self.scenarios:
            if isinstance(s, SupplyShortage) and day >= s.start_day:
                if s.resource == "media":
                    if self._inventory.media_units > s.remaining_units:
                        self._inventory = Inventory(
                            media_units=s.remaining_units,
                            viral_vector_doses=self._inventory.viral_vector_doses,
                            reagent_kits=self._inventory.reagent_kits,
                        )
                elif s.resource == "viral_vector":
                    if self._inventory.viral_vector_doses > s.remaining_units:
                        self._inventory = Inventory(
                            media_units=self._inventory.media_units,
                            viral_vector_doses=s.remaining_units,
                            reagent_kits=self._inventory.reagent_kits,
                        )
                elif s.resource == "reagent":
                    if self._inventory.reagent_kits > s.remaining_units:
                        self._inventory = Inventory(
                            media_units=self._inventory.media_units,
                            viral_vector_doses=self._inventory.viral_vector_doses,
                            reagent_kits=s.remaining_units,
                        )

    # ------------------------------------------------------------------
    # Estimation helpers
    # ------------------------------------------------------------------

    def _estimate_days_remaining(self, batch: BatchTracker) -> float:
        """Estimate remaining days for an active batch."""
        current_idx = PHASE_ORDER.index(batch.current_phase)
        remaining = 0.0
        for phase in PHASE_ORDER[current_idx:]:
            remaining += self.phase_durations[phase].mean_days
        return remaining

    def _estimate_variance(self, batch: BatchTracker) -> float:
        """Estimate variance of remaining days."""
        current_idx = PHASE_ORDER.index(batch.current_phase)
        variance = 0.0
        for phase in PHASE_ORDER[current_idx:]:
            cfg = self.phase_durations[phase]
            if cfg.distribution == DistributionType.LOGNORMAL:
                variance += cfg.std_days**2
        return variance


# ---------------------------------------------------------------------------
# Internal suite state (mutable, not exposed via MDP)
# ---------------------------------------------------------------------------

@dataclass
class _SuiteInternal:
    """Mutable internal state for a suite during simulation."""

    suite_id: str
    status: SuiteStatus = SuiteStatus.IDLE
    batch_id: str | None = None
    phase: BatchPhase | None = None
    cleaning_remaining_hours: float = 0.0
