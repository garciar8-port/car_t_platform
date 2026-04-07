"""Baseline scheduling heuristics for benchmarking against the RL agent.

Three deterministic policies:
- FIFO: first patient in, first patient scheduled
- Highest-acuity-first: sickest patient gets priority
- Shortest-processing-time-first: fastest expected batch goes first
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union

from bioflow_scheduler.mdp.schemas import (
    AssignAction,
    NoOpAction,
    State,
)

# Expected total processing days by indication (used by SPT heuristic)
DEFAULT_PROCESSING_TIMES: dict[str, float] = {
    "DLBCL": 21.0,
    "ALL": 18.0,
    "MCL": 23.0,
    "FL": 20.0,
    "CLL": 22.0,
}


class SchedulingPolicy(ABC):
    """Abstract base class for scheduling policies."""

    @abstractmethod
    def select_action(self, state: State) -> Union[AssignAction, NoOpAction]:
        """Given the current state, return an action."""
        ...


class FIFOPolicy(SchedulingPolicy):
    """First-in, first-out: assign the longest-waiting patient to the first idle suite."""

    def select_action(self, state: State) -> Union[AssignAction, NoOpAction]:
        if not state.has_actionable_assignment:
            return NoOpAction()

        # Patient who has been waiting the longest
        patient = max(state.patient_queue, key=lambda p: p.days_waiting)
        suite = state.idle_suites[0]

        return AssignAction(
            patient_id=patient.patient_id,
            suite_id=suite.id,
            start_time=state.clock,
        )


class HighestAcuityFirstPolicy(SchedulingPolicy):
    """Assign the highest-acuity patient first. Ties broken by days waiting."""

    def select_action(self, state: State) -> Union[AssignAction, NoOpAction]:
        if not state.has_actionable_assignment:
            return NoOpAction()

        # Highest acuity, then longest waiting as tiebreaker
        patient = max(
            state.patient_queue,
            key=lambda p: (p.acuity_score, p.days_waiting),
        )
        suite = state.idle_suites[0]

        return AssignAction(
            patient_id=patient.patient_id,
            suite_id=suite.id,
            start_time=state.clock,
        )


class ShortestProcessingTimePolicy(SchedulingPolicy):
    """Assign the patient with the shortest expected processing time first."""

    def __init__(
        self, processing_times: dict[str, float] | None = None
    ) -> None:
        self.processing_times = processing_times or dict(DEFAULT_PROCESSING_TIMES)
        self._default_time = 21.0  # fallback for unknown indications

    def select_action(self, state: State) -> Union[AssignAction, NoOpAction]:
        if not state.has_actionable_assignment:
            return NoOpAction()

        # Shortest expected processing time
        patient = min(
            state.patient_queue,
            key=lambda p: self.processing_times.get(p.indication, self._default_time),
        )
        suite = state.idle_suites[0]

        return AssignAction(
            patient_id=patient.patient_id,
            suite_id=suite.id,
            start_time=state.clock,
        )
