"""Tests for MDP schema definitions.

Covers validation rules, edge cases, computed properties, and reward calculation.
"""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from bioflow_scheduler.mdp import (
    AssignAction,
    BatchPhase,
    FacilityConfig,
    IncomingPatient,
    Inventory,
    NoOpAction,
    Patient,
    Reward,
    RewardWeights,
    State,
    Suite,
    SuiteStatus,
    TransitionDistributions,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def idle_suite() -> Suite:
    return Suite(id="SUITE-01", status=SuiteStatus.IDLE)


@pytest.fixture
def in_use_suite() -> Suite:
    return Suite(
        id="SUITE-02",
        status=SuiteStatus.IN_USE,
        current_batch_id="B-1001",
        current_phase=BatchPhase.EXPANSION,
        days_remaining_estimate=5.0,
        days_remaining_variance=1.2,
    )


@pytest.fixture
def patient() -> Patient:
    return Patient(
        patient_id="PT-2401",
        indication="DLBCL",
        acuity_score=0.72,
        days_waiting=3,
        cell_viability_days_remaining=14,
        cells_collected_date=date(2026, 4, 3),
    )


@pytest.fixture
def inventory() -> Inventory:
    return Inventory(media_units=50, viral_vector_doses=20, reagent_kits=30)


@pytest.fixture
def basic_state(idle_suite: Suite, in_use_suite: Suite, patient: Patient, inventory: Inventory) -> State:
    return State(
        suites=[idle_suite, in_use_suite],
        patient_queue=[patient],
        inventory=inventory,
        clock=datetime(2026, 4, 6, 8, 0),
    )


# ---------------------------------------------------------------------------
# Suite tests
# ---------------------------------------------------------------------------

class TestSuite:
    def test_idle_suite_valid(self, idle_suite: Suite) -> None:
        assert idle_suite.status == SuiteStatus.IDLE
        assert idle_suite.current_batch_id is None
        assert idle_suite.current_phase is None

    def test_in_use_suite_valid(self, in_use_suite: Suite) -> None:
        assert in_use_suite.status == SuiteStatus.IN_USE
        assert in_use_suite.current_batch_id == "B-1001"
        assert in_use_suite.current_phase == BatchPhase.EXPANSION

    def test_idle_suite_with_batch_fails(self) -> None:
        with pytest.raises(ValidationError, match="Idle suite must not have a current_batch_id"):
            Suite(
                id="SUITE-01",
                status=SuiteStatus.IDLE,
                current_batch_id="B-1001",
            )

    def test_idle_suite_with_phase_fails(self) -> None:
        with pytest.raises(ValidationError, match="Idle suite must not have a current_phase"):
            Suite(
                id="SUITE-01",
                status=SuiteStatus.IDLE,
                current_phase=BatchPhase.EXPANSION,
            )

    def test_in_use_suite_without_batch_fails(self) -> None:
        with pytest.raises(ValidationError, match="In-use suite must have a current_batch_id"):
            Suite(
                id="SUITE-01",
                status=SuiteStatus.IN_USE,
                current_phase=BatchPhase.QC,
            )

    def test_in_use_suite_without_phase_fails(self) -> None:
        with pytest.raises(ValidationError, match="In-use suite must have a current_phase"):
            Suite(
                id="SUITE-01",
                status=SuiteStatus.IN_USE,
                current_batch_id="B-1001",
            )

    def test_cleaning_suite_no_batch_required(self) -> None:
        suite = Suite(id="SUITE-01", status=SuiteStatus.CLEANING)
        assert suite.status == SuiteStatus.CLEANING

    def test_maintenance_suite_no_batch_required(self) -> None:
        suite = Suite(id="SUITE-01", status=SuiteStatus.MAINTENANCE)
        assert suite.status == SuiteStatus.MAINTENANCE

    def test_negative_days_remaining_fails(self) -> None:
        with pytest.raises(ValidationError):
            Suite(id="SUITE-01", status=SuiteStatus.IDLE, days_remaining_estimate=-1.0)


# ---------------------------------------------------------------------------
# Patient tests
# ---------------------------------------------------------------------------

class TestPatient:
    def test_valid_patient(self, patient: Patient) -> None:
        assert patient.patient_id == "PT-2401"
        assert patient.acuity_score == 0.72

    def test_acuity_score_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Patient(
                patient_id="PT-0001",
                indication="ALL",
                acuity_score=1.5,
                days_waiting=0,
                cell_viability_days_remaining=14,
            )
        with pytest.raises(ValidationError):
            Patient(
                patient_id="PT-0001",
                indication="ALL",
                acuity_score=-0.1,
                days_waiting=0,
                cell_viability_days_remaining=14,
            )

    def test_acuity_score_edge_values(self) -> None:
        p_min = Patient(
            patient_id="PT-0001",
            indication="ALL",
            acuity_score=0.0,
            days_waiting=0,
            cell_viability_days_remaining=14,
        )
        p_max = Patient(
            patient_id="PT-0002",
            indication="DLBCL",
            acuity_score=1.0,
            days_waiting=0,
            cell_viability_days_remaining=14,
        )
        assert p_min.acuity_score == 0.0
        assert p_max.acuity_score == 1.0

    def test_negative_days_waiting_fails(self) -> None:
        with pytest.raises(ValidationError):
            Patient(
                patient_id="PT-0001",
                indication="ALL",
                acuity_score=0.5,
                days_waiting=-1,
                cell_viability_days_remaining=14,
            )

    def test_patient_without_collection_dates(self) -> None:
        p = Patient(
            patient_id="PT-0001",
            indication="MCL",
            acuity_score=0.3,
            days_waiting=0,
            cell_viability_days_remaining=21,
            scheduled_leukapheresis_date=date(2026, 4, 10),
        )
        assert p.cells_collected_date is None
        assert p.scheduled_leukapheresis_date == date(2026, 4, 10)


# ---------------------------------------------------------------------------
# State tests
# ---------------------------------------------------------------------------

class TestState:
    def test_basic_state(self, basic_state: State) -> None:
        assert len(basic_state.suites) == 2
        assert basic_state.num_patients_waiting == 1
        assert basic_state.num_idle_suites == 1
        assert basic_state.has_actionable_assignment is True

    def test_empty_queue_not_actionable(self, idle_suite: Suite, inventory: Inventory) -> None:
        state = State(
            suites=[idle_suite],
            patient_queue=[],
            inventory=inventory,
            clock=datetime(2026, 4, 6, 8, 0),
        )
        assert state.has_actionable_assignment is False
        assert state.num_patients_waiting == 0

    def test_no_idle_suites_not_actionable(
        self, in_use_suite: Suite, patient: Patient, inventory: Inventory
    ) -> None:
        state = State(
            suites=[in_use_suite],
            patient_queue=[patient],
            inventory=inventory,
            clock=datetime(2026, 4, 6, 8, 0),
        )
        assert state.has_actionable_assignment is False
        assert state.num_idle_suites == 0

    def test_full_facility(self, patient: Patient, inventory: Inventory) -> None:
        """All suites in use — a realistic stress scenario."""
        suites = [
            Suite(
                id=f"SUITE-{i:02d}",
                status=SuiteStatus.IN_USE,
                current_batch_id=f"B-{1000 + i}",
                current_phase=BatchPhase.EXPANSION,
                days_remaining_estimate=float(i + 1),
            )
            for i in range(6)
        ]
        state = State(
            suites=suites,
            patient_queue=[patient],
            inventory=inventory,
            clock=datetime(2026, 4, 6, 8, 0),
        )
        assert state.num_idle_suites == 0
        assert state.has_actionable_assignment is False
        assert len(state.suites) == 6

    def test_state_requires_at_least_one_suite(self, inventory: Inventory) -> None:
        with pytest.raises(ValidationError):
            State(
                suites=[],
                inventory=inventory,
                clock=datetime(2026, 4, 6, 8, 0),
            )

    def test_idle_suites_property(self, basic_state: State) -> None:
        idle = basic_state.idle_suites
        assert len(idle) == 1
        assert idle[0].id == "SUITE-01"


# ---------------------------------------------------------------------------
# Action tests
# ---------------------------------------------------------------------------

class TestActions:
    def test_assign_action(self) -> None:
        action = AssignAction(
            patient_id="PT-2401",
            suite_id="SUITE-01",
            start_time=datetime(2026, 4, 6, 12, 0),
        )
        assert action.type == "assign"
        assert action.patient_id == "PT-2401"

    def test_no_op_action(self) -> None:
        action = NoOpAction()
        assert action.type == "no_op"


# ---------------------------------------------------------------------------
# Reward tests
# ---------------------------------------------------------------------------

class TestReward:
    def test_default_weights(self) -> None:
        w = RewardWeights()
        assert w.wait_time == 1.0
        assert w.idle_time == 0.2
        assert w.batch_failure == 50.0
        assert w.successful_infusion == 100.0
        assert w.constraint_violation == 1000.0

    def test_reward_compute_successful_infusion(self) -> None:
        w = RewardWeights()
        r = Reward.compute(w, successful_infusions=1)
        assert r.total == 100.0
        assert r.components.infusion_reward == 100.0
        assert r.components.wait_time_penalty == 0.0

    def test_reward_compute_wait_penalty(self) -> None:
        w = RewardWeights()
        r = Reward.compute(w, wait_time_days=5.0)
        assert r.total == -5.0
        assert r.components.wait_time_penalty == -5.0

    def test_reward_compute_constraint_violation(self) -> None:
        w = RewardWeights()
        r = Reward.compute(w, constraint_violations=1)
        assert r.total == -1000.0

    def test_reward_compute_mixed(self) -> None:
        w = RewardWeights()
        r = Reward.compute(
            w,
            wait_time_days=2.0,
            idle_time_days=1.0,
            batch_failures=0,
            successful_infusions=1,
            constraint_violations=0,
        )
        # -1.0*2.0 + -0.2*1.0 + 100.0 = -2.0 - 0.2 + 100.0 = 97.8
        assert r.total == pytest.approx(97.8)

    def test_reward_compute_batch_failure(self) -> None:
        w = RewardWeights()
        r = Reward.compute(w, batch_failures=1)
        assert r.total == -50.0
        assert r.components.batch_failure_penalty == -50.0

    def test_reward_custom_weights(self) -> None:
        w = RewardWeights(wait_time=2.0, successful_infusion=200.0)
        r = Reward.compute(w, wait_time_days=3.0, successful_infusions=1)
        # -2.0*3.0 + 200.0 = 194.0
        assert r.total == pytest.approx(194.0)

    def test_reward_zero_case(self) -> None:
        w = RewardWeights()
        r = Reward.compute(w)
        assert r.total == 0.0


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestConfig:
    def test_default_facility_config(self) -> None:
        config = FacilityConfig()
        assert config.num_suites == 6
        assert config.discount_factor == 0.95
        assert config.seed is None

    def test_facility_config_with_seed(self) -> None:
        config = FacilityConfig(seed=42)
        assert config.seed == 42

    def test_transition_distributions_defaults(self) -> None:
        td = TransitionDistributions()
        assert td.qc_pass_probability == 0.90  # FDA BLA reviews: Kymriah ~90%
        assert td.patient_arrival_rate == 0.3  # ~2.1/week for mid-size CDMO

    def test_qc_probability_bounds(self) -> None:
        with pytest.raises(ValidationError):
            TransitionDistributions(qc_pass_probability=1.5)
        with pytest.raises(ValidationError):
            TransitionDistributions(qc_pass_probability=-0.1)

    def test_facility_config_suite_bounds(self) -> None:
        with pytest.raises(ValidationError):
            FacilityConfig(num_suites=0)
        with pytest.raises(ValidationError):
            FacilityConfig(num_suites=51)

    def test_config_serialization_roundtrip(self) -> None:
        config = FacilityConfig(num_suites=4, seed=123)
        json_str = config.model_dump_json()
        restored = FacilityConfig.model_validate_json(json_str)
        assert restored.num_suites == config.num_suites
        assert restored.seed == config.seed
        assert restored.reward_weights.wait_time == config.reward_weights.wait_time


# ---------------------------------------------------------------------------
# Incoming patient & inventory tests
# ---------------------------------------------------------------------------

class TestIncomingPatient:
    def test_valid(self) -> None:
        p = IncomingPatient(patient_id="PT-2500", estimated_arrival_days=5, priority=0.6)
        assert p.estimated_arrival_days == 5

    def test_priority_bounds(self) -> None:
        with pytest.raises(ValidationError):
            IncomingPatient(patient_id="PT-2500", estimated_arrival_days=5, priority=1.1)


class TestInventory:
    def test_valid(self, inventory: Inventory) -> None:
        assert inventory.media_units == 50

    def test_negative_inventory_fails(self) -> None:
        with pytest.raises(ValidationError):
            Inventory(media_units=-1, viral_vector_doses=10, reagent_kits=10)
