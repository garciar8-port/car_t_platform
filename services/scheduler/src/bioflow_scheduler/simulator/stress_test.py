"""Stress test runner for CAR-T scheduling agents.

Evaluates agent robustness under adversarial conditions by comparing
performance with and without stress scenarios active.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from bioflow_scheduler.mdp.schemas import FacilityConfig
from bioflow_scheduler.policy.ppo_agent import EvaluationResults, PPOSchedulingAgent
from bioflow_scheduler.simulator.gymnasium_env import CARTSchedulingEnv
from bioflow_scheduler.simulator.scenarios import STANDARD_SCENARIOS, ScenarioType


class StressTestResult(BaseModel):
    """Results from a single stress scenario evaluation."""

    scenario_name: str
    scenario_description: str
    baseline: dict[str, Any]
    stressed: dict[str, Any]
    degradation_pct: dict[str, float] = Field(
        default_factory=dict,
        description="Percentage change in each metric (negative = worse)",
    )


class StressTestReport(BaseModel):
    """Full report from running the stress test battery."""

    agent_path: str | None = None
    n_episodes: int
    scenarios: list[StressTestResult]

    def summary_table(self) -> str:
        """Format results as a readable table."""
        lines = [
            f"{'Scenario':<35} {'Reward Δ':>10} {'Infusions Δ':>12} {'Failures Δ':>12}",
            "-" * 75,
        ]
        for s in self.scenarios:
            r_pct = s.degradation_pct.get("reward", 0)
            i_pct = s.degradation_pct.get("infusions", 0)
            f_pct = s.degradation_pct.get("failures", 0)
            lines.append(
                f"{s.scenario_name:<35} {r_pct:>+9.1f}% {i_pct:>+11.1f}% {f_pct:>+11.1f}%"
            )
        return "\n".join(lines)


def _evaluate_with_scenarios(
    agent: PPOSchedulingAgent,
    scenarios: list[ScenarioType],
    n_episodes: int,
    seed: int,
) -> dict[str, Any]:
    """Run agent evaluation with stress scenarios active."""
    from bioflow_scheduler.simulator.environment import ManufacturingSimulator

    fc = agent.config.facility_config
    episode_rewards: list[float] = []
    episode_infusions: list[int] = []
    episode_failures: list[int] = []

    for i in range(n_episodes):
        ep_config = FacilityConfig(**{**fc.model_dump(), "seed": seed + i})
        sim = ManufacturingSimulator(ep_config, scenarios=scenarios)

        env = CARTSchedulingEnv(ep_config, max_patients=agent.config.max_patients)
        # Replace the env's internal simulator with our scenario-aware one
        env._sim = sim

        obs, _ = env.reset()
        total_reward = 0.0
        done = False

        while not done:
            action = agent.predict(obs, action_masks=env.action_masks())
            obs, reward, done, _, info = env.step(action)
            total_reward += reward

        episode_rewards.append(total_reward)
        episode_infusions.append(info.get("total_infusions", 0))
        episode_failures.append(info.get("total_failures", 0))

    return {
        "mean_reward": float(np.mean(episode_rewards)),
        "std_reward": float(np.std(episode_rewards)),
        "mean_infusions": float(np.mean(episode_infusions)),
        "std_infusions": float(np.std(episode_infusions)),
        "mean_failures": float(np.mean(episode_failures)),
    }


def run_stress_test(
    agent: PPOSchedulingAgent,
    scenarios: list[ScenarioType] | None = None,
    n_episodes: int = 20,
    seed: int = 42,
    output_path: Path | None = None,
) -> StressTestReport:
    """Run the standard stress test battery against a trained agent.

    Compares agent performance under each scenario vs. baseline (no scenarios).
    """
    if scenarios is None:
        scenarios = STANDARD_SCENARIOS

    # Baseline evaluation (no scenarios)
    print("Evaluating baseline (no stress)...")
    baseline_results = agent.evaluate(n_episodes=n_episodes, seed=seed)
    baseline = baseline_results.summary()

    results: list[StressTestResult] = []

    for scenario in scenarios:
        print(f"Evaluating: {scenario.name}...")
        stressed = _evaluate_with_scenarios(
            agent, [scenario], n_episodes, seed
        )

        # Compute degradation percentages
        degradation: dict[str, float] = {}
        for metric in ["mean_reward", "mean_infusions", "mean_failures"]:
            base_val = baseline[metric]
            stress_val = stressed[metric]
            if abs(base_val) > 0.01:
                degradation[metric.replace("mean_", "")] = (
                    (stress_val - base_val) / abs(base_val) * 100
                )
            else:
                degradation[metric.replace("mean_", "")] = 0.0

        results.append(
            StressTestResult(
                scenario_name=scenario.name,
                scenario_description=scenario.description,
                baseline=baseline,
                stressed=stressed,
                degradation_pct=degradation,
            )
        )

    report = StressTestReport(
        n_episodes=n_episodes,
        scenarios=results,
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report.model_dump_json(indent=2))
        print(f"Report saved to {output_path}")

    return report
