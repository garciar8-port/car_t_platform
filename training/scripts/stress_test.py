"""Run stress tests against a trained PPO agent.

Usage:
    python training/scripts/stress_test.py --model training/results/ppo_mvp_v2
    python training/scripts/stress_test.py --model training/results/ppo_mvp_v2 --episodes 50
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "scheduler" / "src"))

from bioflow_scheduler.policy.ppo_agent import PPOSchedulingAgent
from bioflow_scheduler.simulator.stress_test import run_stress_test


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test a trained agent")
    parser.add_argument("--model", type=str, required=True, help="Path to saved model")
    parser.add_argument("--episodes", type=int, default=20, help="Episodes per scenario")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("=" * 75)
    print("BioFlow Scheduler — Adversarial Stress Testing")
    print("=" * 75)

    agent = PPOSchedulingAgent.load(args.model)
    print(f"Loaded agent from {args.model}")

    output_path = Path(args.model) / "stress_test_report.json"

    report = run_stress_test(
        agent,
        n_episodes=args.episodes,
        seed=args.seed,
        output_path=output_path,
    )

    print("\n" + "=" * 75)
    print("Stress Test Results")
    print("=" * 75)
    print(report.summary_table())


if __name__ == "__main__":
    main()
