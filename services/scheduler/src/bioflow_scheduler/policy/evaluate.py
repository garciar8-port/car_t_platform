"""Evaluate and compare scheduling policies (PPO vs baselines).

Provides statistical comparison with significance testing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from bioflow_scheduler.mdp.schemas import FacilityConfig
from bioflow_scheduler.simulator.environment import ManufacturingSimulator
from bioflow_scheduler.simulator.gymnasium_env import CARTSchedulingEnv
from bioflow_scheduler.simulator.heuristics import (
    FIFOPolicy,
    HighestAcuityFirstPolicy,
    SchedulingPolicy,
    ShortestProcessingTimePolicy,
)
from bioflow_scheduler.policy.ppo_agent import EvaluationResults, PPOSchedulingAgent


def evaluate_heuristic(
    policy: SchedulingPolicy,
    facility_config: FacilityConfig,
    n_episodes: int = 100,
    base_seed: int = 0,
) -> EvaluationResults:
    """Evaluate a heuristic policy over multiple episodes."""
    episode_rewards: list[float] = []
    episode_infusions: list[int] = []
    episode_failures: list[int] = []
    episode_queue_sizes: list[int] = []

    for i in range(n_episodes):
        config = FacilityConfig(**{**facility_config.model_dump(), "seed": base_seed + i})
        sim = ManufacturingSimulator(config)
        state = sim.reset()
        total_reward = 0.0

        while True:
            action = policy.select_action(state)
            state, reward, done, info = sim.step(action)
            total_reward += reward.total
            if done:
                break

        episode_rewards.append(total_reward)
        episode_infusions.append(info.get("total_infusions", 0))
        episode_failures.append(info.get("total_failures", 0))
        episode_queue_sizes.append(state.num_patients_waiting)

    return EvaluationResults(
        n_episodes=n_episodes,
        mean_reward=float(np.mean(episode_rewards)),
        std_reward=float(np.std(episode_rewards)),
        mean_infusions=float(np.mean(episode_infusions)),
        std_infusions=float(np.std(episode_infusions)),
        mean_failures=float(np.mean(episode_failures)),
        mean_queue_size=float(np.mean(episode_queue_sizes)),
        all_rewards=episode_rewards,
        all_infusions=[int(x) for x in episode_infusions],
        all_failures=[int(x) for x in episode_failures],
    )


@dataclass
class ComparisonResult:
    """Statistical comparison between two policies."""

    policy_a: str
    policy_b: str
    metric: str
    mean_a: float
    mean_b: float
    difference: float
    p_value: float
    significant: bool  # p < 0.05

    def __str__(self) -> str:
        sig = "***" if self.significant else "(n.s.)"
        return (
            f"{self.metric}: {self.policy_a}={self.mean_a:.1f} vs "
            f"{self.policy_b}={self.mean_b:.1f} "
            f"(diff={self.difference:+.1f}, p={self.p_value:.4f}) {sig}"
        )


def compare_policies(
    results_a: EvaluationResults,
    results_b: EvaluationResults,
    name_a: str = "Policy A",
    name_b: str = "Policy B",
) -> list[ComparisonResult]:
    """Statistical comparison between two policies using Welch's t-test."""
    comparisons = []

    for metric, vals_a, vals_b in [
        ("reward", results_a.all_rewards, results_b.all_rewards),
        ("infusions", results_a.all_infusions, results_b.all_infusions),
        ("failures", results_a.all_failures, results_b.all_failures),
    ]:
        t_stat, p_value = stats.ttest_ind(vals_a, vals_b, equal_var=False)
        mean_a = float(np.mean(vals_a))
        mean_b = float(np.mean(vals_b))

        comparisons.append(
            ComparisonResult(
                policy_a=name_a,
                policy_b=name_b,
                metric=metric,
                mean_a=mean_a,
                mean_b=mean_b,
                difference=mean_a - mean_b,
                p_value=float(p_value),
                significant=p_value < 0.05,
            )
        )

    return comparisons


def run_full_benchmark(
    agent: PPOSchedulingAgent,
    facility_config: FacilityConfig | None = None,
    n_episodes: int = 100,
    base_seed: int = 1000,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run PPO against all baselines and produce a comparison report.

    Returns a dict with results for each policy and statistical comparisons.
    """
    fc = facility_config or agent.config.facility_config

    # Evaluate all policies on the same set of seeds
    print("Evaluating PPO agent...")
    ppo_results = agent.evaluate(
        n_episodes=n_episodes, seed=base_seed, facility_config=fc
    )
    print(f"  PPO: {ppo_results}")

    baselines = {
        "FIFO": FIFOPolicy(),
        "Highest Acuity": HighestAcuityFirstPolicy(),
        "Shortest Processing": ShortestProcessingTimePolicy(),
    }

    baseline_results: dict[str, EvaluationResults] = {}
    for name, policy in baselines.items():
        print(f"Evaluating {name}...")
        baseline_results[name] = evaluate_heuristic(
            policy, fc, n_episodes=n_episodes, base_seed=base_seed
        )
        print(f"  {name}: {baseline_results[name]}")

    # Statistical comparisons
    print("\n=== Statistical Comparisons ===")
    all_comparisons: dict[str, list[dict]] = {}
    for name, baseline in baseline_results.items():
        comps = compare_policies(ppo_results, baseline, "PPO", name)
        all_comparisons[name] = []
        for c in comps:
            print(f"  {c}")
            all_comparisons[name].append({
                "metric": c.metric,
                "ppo_mean": c.mean_a,
                "baseline_mean": c.mean_b,
                "difference": c.difference,
                "p_value": c.p_value,
                "significant": c.significant,
            })

    report = {
        "n_episodes": n_episodes,
        "facility_config": fc.model_dump(),
        "results": {
            "PPO": ppo_results.summary(),
            **{name: r.summary() for name, r in baseline_results.items()},
        },
        "comparisons": all_comparisons,
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"\nReport saved to {output_path}")

    return report
