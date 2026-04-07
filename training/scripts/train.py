"""Train a PPO agent for CAR-T manufacturing scheduling.

Usage:
    python training/scripts/train.py                           # default config
    python training/scripts/train.py --config training/configs/ppo_mvp.json
    python training/scripts/train.py --timesteps 100000        # quick test
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add src to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "scheduler" / "src"))

from bioflow_scheduler.policy.ppo_agent import PPOSchedulingAgent, TrainingConfig
from bioflow_scheduler.policy.evaluate import run_full_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PPO for CAR-T scheduling")
    parser.add_argument("--config", type=str, help="Path to training config JSON")
    parser.add_argument("--timesteps", type=int, help="Override total_timesteps")
    parser.add_argument("--eval-episodes", type=int, default=50, help="Evaluation episodes")
    parser.add_argument("--save-path", type=str, help="Override model save path")
    args = parser.parse_args()

    # Load config
    if args.config:
        config_data = json.loads(Path(args.config).read_text())
        config = TrainingConfig(**config_data)
    else:
        config = TrainingConfig()

    if args.timesteps:
        config = config.model_copy(update={"total_timesteps": args.timesteps})
    if args.save_path:
        config = config.model_copy(update={"save_path": args.save_path})

    print("=" * 60)
    print("BioFlow Scheduler — PPO Training")
    print("=" * 60)
    print(f"Timesteps:    {config.total_timesteps:,}")
    print(f"Suites:       {config.facility_config.num_suites}")
    print(f"Episode days: {config.facility_config.max_episode_days}")
    print(f"Seed:         {config.seed}")
    print(f"Save path:    {config.save_path}")
    print("=" * 60)

    # Train
    agent = PPOSchedulingAgent(config)
    start = time.time()
    metrics = agent.train()
    elapsed = time.time() - start

    print(f"\nTraining completed in {elapsed:.1f}s")
    print(f"Episodes completed: {len(metrics.episode_rewards)}")
    if metrics.episode_rewards:
        print(f"Final 10 episode rewards: {[round(r, 1) for r in metrics.episode_rewards[-10:]]}")

    # Save
    agent.save(config.save_path)
    print(f"Model saved to {config.save_path}/")

    # Evaluate against baselines
    print("\n" + "=" * 60)
    print("Benchmark: PPO vs Baselines")
    print("=" * 60)
    report = run_full_benchmark(
        agent,
        n_episodes=args.eval_episodes,
        output_path=Path(config.save_path) / "benchmark.json",
    )

    # Print summary table
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"{'Policy':<25} {'Reward':>10} {'Infusions':>10} {'Failures':>10}")
    print("-" * 60)
    for name, result in report["results"].items():
        print(
            f"{name:<25} {result['mean_reward']:>10.1f} "
            f"{result['mean_infusions']:>10.1f} {result['mean_failures']:>10.1f}"
        )


if __name__ == "__main__":
    main()
