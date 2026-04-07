"""Tests for the CAR-T manufacturing simulator.

Covers: core simulation, reproducibility, Gymnasium wrapper, heuristics,
and baseline benchmarks.
"""

from __future__ import annotations

import time
from datetime import date

import numpy as np
import pytest

from bioflow_scheduler.mdp.schemas import (
    AssignAction,
    FacilityConfig,
    Inventory,
    NoOpAction,
    Patient,
    State,
    Suite,
    SuiteStatus,
)
from bioflow_scheduler.simulator.environment import ManufacturingSimulator
from bioflow_scheduler.simulator.gymnasium_env import CARTSchedulingEnv
from bioflow_scheduler.simulator.heuristics import (
    FIFOPolicy,
    HighestAcuityFirstPolicy,
    ShortestProcessingTimePolicy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config() -> FacilityConfig:
    return FacilityConfig(
        num_suites=2,
        seed=42,
        max_episode_days=30,
        decision_interval_hours=8.0,
    )


@pytest.fixture
def sim(config: FacilityConfig) -> ManufacturingSimulator:
    s = ManufacturingSimulator(config)
    return s


# ---------------------------------------------------------------------------
# ManufacturingSimulator tests
# ---------------------------------------------------------------------------

class TestManufacturingSimulator:
    def test_reset_returns_valid_state(self, sim: ManufacturingSimulator) -> None:
        state = sim.reset()
        assert isinstance(state, State)
        assert len(state.suites) == 2
        assert state.num_patients_waiting >= 1
        assert state.inventory.media_units > 0

    def test_all_suites_idle_after_reset(self, sim: ManufacturingSimulator) -> None:
        state = sim.reset()
        for suite in state.suites:
            assert suite.status == SuiteStatus.IDLE

    def test_deterministic_with_seed(self, config: FacilityConfig) -> None:
        """Two simulators with same seed produce identical trajectories."""
        sim1 = ManufacturingSimulator(config)
        sim2 = ManufacturingSimulator(config)

        state1 = sim1.reset()
        state2 = sim2.reset()

        assert state1.num_patients_waiting == state2.num_patients_waiting
        assert state1.patient_queue[0].patient_id == state2.patient_queue[0].patient_id

        # Take the same actions
        for _ in range(5):
            s1, r1, d1, _ = sim1.step(NoOpAction())
            s2, r2, d2, _ = sim2.step(NoOpAction())
            assert r1.total == r2.total
            assert s1.num_patients_waiting == s2.num_patients_waiting

    def test_different_seeds_diverge(self) -> None:
        config1 = FacilityConfig(num_suites=2, seed=42, max_episode_days=30)
        config2 = FacilityConfig(num_suites=2, seed=99, max_episode_days=30)

        sim1 = ManufacturingSimulator(config1)
        sim2 = ManufacturingSimulator(config2)

        state1 = sim1.reset()
        state2 = sim2.reset()

        # With different seeds, patient attributes should differ
        if state1.num_patients_waiting > 0 and state2.num_patients_waiting > 0:
            p1 = state1.patient_queue[0]
            p2 = state2.patient_queue[0]
            # At least one attribute should differ
            assert (
                p1.acuity_score != p2.acuity_score
                or p1.indication != p2.indication
                or p1.cell_viability_days_remaining != p2.cell_viability_days_remaining
            )

    def test_noop_advances_time(self, sim: ManufacturingSimulator) -> None:
        state0 = sim.reset()
        state1, _, _, info = sim.step(NoOpAction())
        hours_elapsed = (state1.clock - state0.clock).total_seconds() / 3600
        assert hours_elapsed == pytest.approx(8.0)

    def test_assign_starts_batch(self, sim: ManufacturingSimulator) -> None:
        state = sim.reset()
        assert state.has_actionable_assignment

        patient = state.patient_queue[0]
        suite = state.idle_suites[0]

        action = AssignAction(
            patient_id=patient.patient_id,
            suite_id=suite.id,
            start_time=state.clock,
        )
        new_state, reward, done, info = sim.step(action)

        # Patient removed from queue
        patient_ids = [p.patient_id for p in new_state.patient_queue]
        assert patient.patient_id not in patient_ids

        # Suite is now in use
        assigned_suite = next(s for s in new_state.suites if s.id == suite.id)
        assert assigned_suite.status == SuiteStatus.IN_USE
        assert assigned_suite.current_batch_id is not None
        assert assigned_suite.current_phase is not None

        # No constraint violations
        assert reward.components.constraint_violation_penalty == 0.0

    def test_invalid_assign_nonexistent_patient(self, sim: ManufacturingSimulator) -> None:
        sim.reset()
        action = AssignAction(
            patient_id="PT-FAKE",
            suite_id="SUITE-01",
            start_time=sim._build_state().clock,
        )
        _, reward, _, _ = sim.step(action)
        assert reward.components.constraint_violation_penalty < 0

    def test_invalid_assign_occupied_suite(self, sim: ManufacturingSimulator) -> None:
        state = sim.reset()
        # Assign first patient to first suite
        p = state.patient_queue[0]
        action1 = AssignAction(
            patient_id=p.patient_id, suite_id="SUITE-01", start_time=state.clock
        )
        state2, _, _, _ = sim.step(action1)

        # Try assigning another patient to the same (now occupied) suite
        if len(state2.patient_queue) > 0:
            p2 = state2.patient_queue[0]
            action2 = AssignAction(
                patient_id=p2.patient_id, suite_id="SUITE-01", start_time=state2.clock
            )
            _, reward, _, _ = sim.step(action2)
            assert reward.components.constraint_violation_penalty < 0

    def test_patient_arrivals_occur(self, sim: ManufacturingSimulator) -> None:
        state = sim.reset()
        initial_count = state.num_patients_waiting

        # Run several steps with no-ops — patients should arrive
        for _ in range(20):
            state, _, _, _ = sim.step(NoOpAction())

        # With Poisson rate 1.8/day and 20 steps of 8h, expect ~48 patient-days
        # of arrivals. Should have more patients than we started with.
        assert state.num_patients_waiting > initial_count

    def test_episode_terminates(self) -> None:
        config = FacilityConfig(num_suites=2, seed=42, max_episode_days=5)
        sim = ManufacturingSimulator(config)
        sim.reset()

        done = False
        steps = 0
        while not done:
            _, _, done, _ = sim.step(NoOpAction())
            steps += 1
            assert steps < 1000, "Episode did not terminate"

        # 5 days * 24h / 8h = 15 decision points
        assert steps == 15

    def test_batch_lifecycle_completes(self) -> None:
        """Run long enough for a batch to complete all phases."""
        config = FacilityConfig(num_suites=2, seed=42, max_episode_days=60)
        sim = ManufacturingSimulator(config)
        state = sim.reset()

        # Assign first patient
        p = state.patient_queue[0]
        action = AssignAction(
            patient_id=p.patient_id, suite_id="SUITE-01", start_time=state.clock
        )
        sim.step(action)

        # Run enough steps for batch to complete (~23 days total)
        total_infusions = 0
        total_failures = 0
        for _ in range(200):
            state, _, done, info = sim.step(NoOpAction())
            total_infusions = info["total_infusions"]
            total_failures = info["total_failures"]
            if done:
                break

        # The batch should have completed (either passed or failed QC)
        assert total_infusions + total_failures >= 1

    def test_reward_penalizes_waiting(self, sim: ManufacturingSimulator) -> None:
        sim.reset()
        # Just do nothing — patients wait, we should get negative reward
        _, reward, _, _ = sim.step(NoOpAction())
        assert reward.components.wait_time_penalty < 0

    def test_inventory_consumed_on_assign(self, sim: ManufacturingSimulator) -> None:
        state = sim.reset()
        initial_media = state.inventory.media_units

        p = state.patient_queue[0]
        action = AssignAction(
            patient_id=p.patient_id, suite_id="SUITE-01", start_time=state.clock
        )
        new_state, _, _, _ = sim.step(action)
        assert new_state.inventory.media_units == initial_media - 1


# ---------------------------------------------------------------------------
# Gymnasium wrapper tests
# ---------------------------------------------------------------------------

class TestGymnasiumEnv:
    def test_observation_shape(self) -> None:
        config = FacilityConfig(num_suites=2, seed=42)
        env = CARTSchedulingEnv(config, max_patients=10)
        obs, _ = env.reset()

        expected = 2 * 14 + 10 * 5 + 3 + 2  # suites + patients + inv + clock
        assert obs.shape == (expected,)

    def test_observation_dtype(self) -> None:
        env = CARTSchedulingEnv(FacilityConfig(num_suites=2, seed=42), max_patients=10)
        obs, _ = env.reset()
        assert obs.dtype == np.float32

    def test_observation_bounds(self) -> None:
        env = CARTSchedulingEnv(FacilityConfig(num_suites=2, seed=42), max_patients=10)
        obs, _ = env.reset()
        assert np.all(obs >= 0.0)
        assert np.all(obs <= 1.0)

    def test_action_space_size(self) -> None:
        config = FacilityConfig(num_suites=3, seed=42)
        env = CARTSchedulingEnv(config, max_patients=15)
        assert env.action_space.n == 15 * 3 + 1  # 46

    def test_step_returns_correct_types(self) -> None:
        env = CARTSchedulingEnv(FacilityConfig(num_suites=2, seed=42), max_patients=10)
        env.reset()
        obs, reward, terminated, truncated, info = env.step(0)  # no-op
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_noop_is_action_zero(self) -> None:
        env = CARTSchedulingEnv(FacilityConfig(num_suites=2, seed=42), max_patients=10)
        env.reset()
        # Action 0 should always work (no-op)
        obs, _, _, _, _ = env.step(0)
        assert obs is not None

    def test_seed_reproducibility(self) -> None:
        env = CARTSchedulingEnv(FacilityConfig(num_suites=2), max_patients=10)

        obs1, _ = env.reset(seed=42)
        obs1_step, r1, _, _, _ = env.step(0)

        obs2, _ = env.reset(seed=42)
        obs2_step, r2, _, _, _ = env.step(0)

        np.testing.assert_array_equal(obs1, obs2)
        np.testing.assert_array_equal(obs1_step, obs2_step)
        assert r1 == r2

    def test_action_masks_shape(self) -> None:
        config = FacilityConfig(num_suites=2, seed=42)
        env = CARTSchedulingEnv(config, max_patients=10)
        env.reset()
        masks = env.action_masks()
        assert masks.shape == (env.action_space.n,)
        assert masks.dtype == bool
        assert masks[0]  # no-op always valid

    def test_gymnasium_check_env(self) -> None:
        """Validate the environment conforms to Gymnasium API."""
        from gymnasium.utils.env_checker import check_env

        env = CARTSchedulingEnv(
            FacilityConfig(num_suites=2, seed=42, max_episode_days=5),
            max_patients=10,
        )
        # check_env will raise if something is wrong
        check_env(env.unwrapped, skip_render_check=True)

    def test_render_text(self) -> None:
        env = CARTSchedulingEnv(
            FacilityConfig(num_suites=2, seed=42),
            max_patients=10,
            render_mode="text",
        )
        env.reset()
        output = env.render()
        assert output is not None
        assert "SUITE-01" in output


# ---------------------------------------------------------------------------
# Heuristic tests
# ---------------------------------------------------------------------------

class TestHeuristics:
    @pytest.fixture
    def two_patient_state(self) -> State:
        """State with 2 patients and 1 idle suite."""
        from datetime import datetime, timezone

        return State(
            suites=[
                Suite(id="SUITE-01", status=SuiteStatus.IDLE),
                Suite(
                    id="SUITE-02",
                    status=SuiteStatus.IN_USE,
                    current_batch_id="B-9999",
                    current_phase="expansion",
                    days_remaining_estimate=5.0,
                ),
            ],
            patient_queue=[
                Patient(
                    patient_id="PT-0001",
                    indication="DLBCL",
                    acuity_score=0.3,
                    days_waiting=5,
                    cell_viability_days_remaining=14,
                ),
                Patient(
                    patient_id="PT-0002",
                    indication="ALL",
                    acuity_score=0.8,
                    days_waiting=2,
                    cell_viability_days_remaining=20,
                ),
            ],
            inventory=Inventory(media_units=10, viral_vector_doses=5, reagent_kits=8),
            clock=datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc),
        )

    def test_fifo_selects_longest_waiting(self, two_patient_state: State) -> None:
        policy = FIFOPolicy()
        action = policy.select_action(two_patient_state)
        assert isinstance(action, AssignAction)
        assert action.patient_id == "PT-0001"  # 5 days waiting vs 2
        assert action.suite_id == "SUITE-01"

    def test_highest_acuity_selects_most_urgent(self, two_patient_state: State) -> None:
        policy = HighestAcuityFirstPolicy()
        action = policy.select_action(two_patient_state)
        assert isinstance(action, AssignAction)
        assert action.patient_id == "PT-0002"  # acuity 0.8 vs 0.3

    def test_shortest_processing_selects_fastest(self, two_patient_state: State) -> None:
        policy = ShortestProcessingTimePolicy()
        action = policy.select_action(two_patient_state)
        assert isinstance(action, AssignAction)
        # ALL = 18 days, DLBCL = 21 days → should pick ALL patient
        assert action.patient_id == "PT-0002"

    def test_noop_when_no_idle_suites(self) -> None:
        from datetime import datetime, timezone

        state = State(
            suites=[
                Suite(
                    id="SUITE-01",
                    status=SuiteStatus.IN_USE,
                    current_batch_id="B-0001",
                    current_phase="expansion",
                ),
            ],
            patient_queue=[
                Patient(
                    patient_id="PT-0001",
                    indication="DLBCL",
                    acuity_score=0.5,
                    days_waiting=3,
                    cell_viability_days_remaining=14,
                ),
            ],
            inventory=Inventory(media_units=10, viral_vector_doses=5, reagent_kits=8),
            clock=datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc),
        )
        for policy in [FIFOPolicy(), HighestAcuityFirstPolicy(), ShortestProcessingTimePolicy()]:
            assert isinstance(policy.select_action(state), NoOpAction)

    def test_noop_when_no_patients(self) -> None:
        from datetime import datetime, timezone

        state = State(
            suites=[Suite(id="SUITE-01", status=SuiteStatus.IDLE)],
            patient_queue=[],
            inventory=Inventory(media_units=10, viral_vector_doses=5, reagent_kits=8),
            clock=datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc),
        )
        for policy in [FIFOPolicy(), HighestAcuityFirstPolicy(), ShortestProcessingTimePolicy()]:
            assert isinstance(policy.select_action(state), NoOpAction)

    def test_acuity_tiebreak_by_wait(self) -> None:
        from datetime import datetime, timezone

        state = State(
            suites=[Suite(id="SUITE-01", status=SuiteStatus.IDLE)],
            patient_queue=[
                Patient(
                    patient_id="PT-0001",
                    indication="DLBCL",
                    acuity_score=0.7,
                    days_waiting=10,
                    cell_viability_days_remaining=14,
                ),
                Patient(
                    patient_id="PT-0002",
                    indication="ALL",
                    acuity_score=0.7,
                    days_waiting=3,
                    cell_viability_days_remaining=20,
                ),
            ],
            inventory=Inventory(media_units=10, viral_vector_doses=5, reagent_kits=8),
            clock=datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc),
        )
        policy = HighestAcuityFirstPolicy()
        action = policy.select_action(state)
        assert isinstance(action, AssignAction)
        assert action.patient_id == "PT-0001"  # same acuity, longer wait

    def test_all_heuristics_deterministic(self, two_patient_state: State) -> None:
        for Policy in [FIFOPolicy, HighestAcuityFirstPolicy, ShortestProcessingTimePolicy]:
            policy = Policy()
            a1 = policy.select_action(two_patient_state)
            a2 = policy.select_action(two_patient_state)
            assert a1 == a2


# ---------------------------------------------------------------------------
# Baseline benchmark tests
# ---------------------------------------------------------------------------

class TestBaselineBenchmarks:
    @pytest.fixture
    def benchmark_config(self) -> FacilityConfig:
        return FacilityConfig(
            num_suites=6,
            seed=42,
            max_episode_days=90,
            decision_interval_hours=8.0,
        )

    def _run_episode(
        self, config: FacilityConfig, policy
    ) -> dict:
        sim = ManufacturingSimulator(config)
        state = sim.reset()
        total_reward = 0.0
        steps = 0

        while True:
            action = policy.select_action(state)
            state, reward, done, info = sim.step(action)
            total_reward += reward.total
            steps += 1
            if done:
                break

        return {
            "total_reward": total_reward,
            "steps": steps,
            "total_infusions": info["total_infusions"],
            "total_failures": info["total_failures"],
            "final_queue_size": state.num_patients_waiting,
            "sim_days": info["sim_time_days"],
        }

    def test_fifo_completes_episode(self, benchmark_config: FacilityConfig) -> None:
        result = self._run_episode(benchmark_config, FIFOPolicy())
        assert result["steps"] > 0
        assert result["total_infusions"] >= 0
        assert result["sim_days"] == pytest.approx(90.0, abs=1.0)

    def test_highest_acuity_completes_episode(self, benchmark_config: FacilityConfig) -> None:
        result = self._run_episode(benchmark_config, HighestAcuityFirstPolicy())
        assert result["steps"] > 0
        assert result["total_infusions"] >= 0

    def test_spt_completes_episode(self, benchmark_config: FacilityConfig) -> None:
        result = self._run_episode(benchmark_config, ShortestProcessingTimePolicy())
        assert result["steps"] > 0
        assert result["total_infusions"] >= 0

    def test_benchmarks_reproducible(self, benchmark_config: FacilityConfig) -> None:
        policy = FIFOPolicy()
        r1 = self._run_episode(benchmark_config, policy)
        r2 = self._run_episode(benchmark_config, policy)
        assert r1["total_reward"] == r2["total_reward"]
        assert r1["total_infusions"] == r2["total_infusions"]
        assert r1["total_failures"] == r2["total_failures"]

    def test_episode_runs_under_30_seconds(self, benchmark_config: FacilityConfig) -> None:
        """Acceptance criterion: 90-day episode completes in under 30s."""
        start = time.time()
        self._run_episode(benchmark_config, FIFOPolicy())
        elapsed = time.time() - start
        assert elapsed < 30.0, f"Episode took {elapsed:.1f}s, exceeds 30s limit"
