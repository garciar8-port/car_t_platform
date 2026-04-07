"""OpenAI Gymnasium wrapper for the CAR-T manufacturing simulator.

Provides the standard reset()/step() interface compatible with
Stable Baselines3 and other RL libraries.
"""

from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from bioflow_scheduler.mdp.schemas import (
    AssignAction,
    BatchPhase,
    FacilityConfig,
    NoOpAction,
    SuiteStatus,
)
from bioflow_scheduler.simulator.environment import ManufacturingSimulator

# Number of features per encoded entity
_SUITE_STATUS_DIM = len(SuiteStatus)    # 4 (one-hot)
_SUITE_PHASE_DIM = len(BatchPhase)      # 7 (one-hot)
_SUITE_NUMERIC_DIM = 3                  # days_remaining, variance, occupied_flag
SUITE_FEATURES = _SUITE_STATUS_DIM + _SUITE_PHASE_DIM + _SUITE_NUMERIC_DIM  # 14

PATIENT_FEATURES = 5  # acuity, days_waiting_norm, viability_norm, has_cells, indication_idx

INVENTORY_FEATURES = 3  # media, vectors, reagents
CLOCK_FEATURES = 2      # day_of_week_norm, hour_of_day_norm

# Normalization constants
MAX_DAYS_REMAINING = 30.0
MAX_VARIANCE = 25.0
MAX_DAYS_WAITING = 90.0
MAX_VIABILITY_DAYS = 30.0
MAX_INVENTORY = 100.0
NUM_INDICATIONS = 5

# SuiteStatus and BatchPhase ordered for consistent one-hot encoding
_STATUS_ORDER = list(SuiteStatus)
_PHASE_ORDER = list(BatchPhase)


class CARTSchedulingEnv(gym.Env):
    """Gymnasium environment for CAR-T manufacturing scheduling.

    Observation: fixed-size float32 vector encoding suites, patient queue,
    inventory, and clock.

    Action: Discrete integer.
        - 0 = no-op
        - 1..N = assign patient_i to suite_j
          Decoded as: action_idx - 1 => (patient_idx, suite_idx)
          where patient_idx = (action_idx - 1) // num_suites
                suite_idx   = (action_idx - 1) % num_suites
    """

    metadata = {"render_modes": ["text"]}

    def __init__(
        self,
        config: FacilityConfig | None = None,
        max_patients: int = 20,
        max_incoming: int = 10,
        render_mode: str | None = None,
    ) -> None:
        super().__init__()
        self.config = config or FacilityConfig()
        self.max_patients = max_patients
        self.max_incoming = max_incoming
        self.render_mode = render_mode

        self._sim = ManufacturingSimulator(self.config)
        self._current_state = None

        num_suites = self.config.num_suites

        # Observation space
        obs_size = (
            num_suites * SUITE_FEATURES
            + max_patients * PATIENT_FEATURES
            + INVENTORY_FEATURES
            + CLOCK_FEATURES
        )
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(obs_size,),
            dtype=np.float32,
        )

        # Action space: 0 = no-op, 1..max_patients*num_suites = assign
        self.action_space = spaces.Discrete(max_patients * num_suites + 1)

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)

        if seed is not None:
            self.config = FacilityConfig(
                **{**self.config.model_dump(), "seed": seed}
            )
            self._sim = ManufacturingSimulator(self.config)

        self._current_state = self._sim.reset()
        obs = self._flatten_state(self._current_state)
        return obs, {"state": self._current_state}

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        assert self._current_state is not None, "Call reset() before step()"

        decoded = self._decode_action(action)
        state, reward, done, info = self._sim.step(decoded)
        self._current_state = state

        obs = self._flatten_state(state)
        info["state"] = state

        return obs, reward.total, done, False, info

    def action_masks(self) -> np.ndarray:
        """Boolean mask of valid actions. True = valid."""
        if self._current_state is None:
            mask = np.zeros(self.action_space.n, dtype=bool)
            mask[0] = True  # no-op always valid
            return mask

        state = self._current_state
        mask = np.zeros(self.action_space.n, dtype=bool)
        mask[0] = True  # no-op always valid

        idle_suite_ids = {s.id for s in state.idle_suites}
        all_suite_ids = [s.id for s in state.suites]

        for p_idx, _patient in enumerate(state.patient_queue[: self.max_patients]):
            for s_idx, suite_id in enumerate(all_suite_ids):
                if suite_id in idle_suite_ids:
                    action_idx = 1 + p_idx * self.config.num_suites + s_idx
                    if action_idx < self.action_space.n:
                        mask[action_idx] = True

        return mask

    def render(self) -> str | None:
        if self.render_mode != "text" or self._current_state is None:
            return None

        state = self._current_state
        lines = [f"=== Time: {state.clock.isoformat()} ==="]
        for s in state.suites:
            status = f"{s.id}: {s.status.value}"
            if s.current_batch_id:
                status += f" [{s.current_batch_id}, {s.current_phase.value if s.current_phase else '?'}]"  # noqa: E501
            lines.append(status)
        lines.append(f"Queue: {len(state.patient_queue)} patients")
        lines.append(
            f"Inventory: media={state.inventory.media_units}, "
            f"vectors={state.inventory.viral_vector_doses}, "
            f"reagents={state.inventory.reagent_kits}"
        )
        output = "\n".join(lines)
        print(output)
        return output

    # ------------------------------------------------------------------
    # Action decoding
    # ------------------------------------------------------------------

    def _decode_action(self, action_idx: int) -> AssignAction | NoOpAction:
        """Map integer action to an Action object."""
        if action_idx == 0:
            return NoOpAction()

        assert self._current_state is not None

        idx = action_idx - 1
        num_suites = self.config.num_suites
        patient_idx = idx // num_suites
        suite_idx = idx % num_suites

        queue = self._current_state.patient_queue
        suites = self._current_state.suites

        # Out-of-range patient or suite → treat as no-op
        if patient_idx >= len(queue) or suite_idx >= len(suites):
            return NoOpAction()

        # If selected suite is not idle, find the first idle suite instead
        # This helps the agent learn assignment behavior even with imperfect
        # suite selection, reducing the effective action space complexity.
        target_suite = suites[suite_idx]
        if target_suite.status != SuiteStatus.IDLE:
            idle = self._current_state.idle_suites
            if idle:
                target_suite = idle[0]
            else:
                return NoOpAction()

        return AssignAction(
            patient_id=queue[patient_idx].patient_id,
            suite_id=target_suite.id,
            start_time=self._current_state.clock,
        )

    # ------------------------------------------------------------------
    # State flattening
    # ------------------------------------------------------------------

    def _flatten_state(self, state) -> np.ndarray:
        """Convert State to a fixed-size float32 observation vector."""
        parts: list[np.ndarray] = []

        # Encode suites (always config.num_suites)
        for suite in state.suites:
            parts.append(self._encode_suite(suite))

        # Encode patient queue (pad/truncate to max_patients)
        for i in range(self.max_patients):
            if i < len(state.patient_queue):
                parts.append(self._encode_patient(state.patient_queue[i]))
            else:
                parts.append(np.zeros(PATIENT_FEATURES, dtype=np.float32))

        # Inventory (normalized)
        parts.append(
            np.array(
                [
                    min(state.inventory.media_units / MAX_INVENTORY, 1.0),
                    min(state.inventory.viral_vector_doses / MAX_INVENTORY, 1.0),
                    min(state.inventory.reagent_kits / MAX_INVENTORY, 1.0),
                ],
                dtype=np.float32,
            )
        )

        # Clock (normalized)
        parts.append(
            np.array(
                [
                    state.clock.weekday() / 6.0,
                    state.clock.hour / 23.0,
                ],
                dtype=np.float32,
            )
        )

        return np.concatenate(parts)

    def _encode_suite(self, suite) -> np.ndarray:
        """Encode a single suite as a fixed-size vector."""
        vec = np.zeros(SUITE_FEATURES, dtype=np.float32)

        # Status one-hot (4)
        status_idx = _STATUS_ORDER.index(suite.status)
        vec[status_idx] = 1.0

        # Phase one-hot (7) — only if in use
        offset = _SUITE_STATUS_DIM
        if suite.current_phase is not None:
            phase_idx = _PHASE_ORDER.index(suite.current_phase)
            vec[offset + phase_idx] = 1.0

        # Numeric features
        offset += _SUITE_PHASE_DIM
        vec[offset] = min(suite.days_remaining_estimate / MAX_DAYS_REMAINING, 1.0)
        vec[offset + 1] = min(suite.days_remaining_variance / MAX_VARIANCE, 1.0)
        vec[offset + 2] = 1.0 if suite.current_batch_id is not None else 0.0

        return vec

    def _encode_patient(self, patient) -> np.ndarray:
        """Encode a single patient as a fixed-size vector."""
        # Map indication to a normalized index
        indication_map = {"DLBCL": 0, "ALL": 1, "MCL": 2, "FL": 3, "CLL": 4}
        indication_idx = indication_map.get(patient.indication, 0)

        return np.array(
            [
                patient.acuity_score,
                min(patient.days_waiting / MAX_DAYS_WAITING, 1.0),
                min(patient.cell_viability_days_remaining / MAX_VIABILITY_DAYS, 1.0),
                1.0 if patient.cells_collected_date is not None else 0.0,
                indication_idx / max(NUM_INDICATIONS - 1, 1),
            ],
            dtype=np.float32,
        )
