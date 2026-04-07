"""PPO agent wrapper for CAR-T scheduling.

Thin wrapper around Stable Baselines3 MaskablePPO that handles training,
evaluation, saving/loading, and comparison against baselines.
Uses action masking to restrict the agent to only valid actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field
from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
from stable_baselines3.common.callbacks import BaseCallback

from bioflow_scheduler.mdp.schemas import FacilityConfig
from bioflow_scheduler.simulator.gymnasium_env import CARTSchedulingEnv


# ---------------------------------------------------------------------------
# Training configuration
# ---------------------------------------------------------------------------

class TrainingConfig(BaseModel):
    """Hyperparameters for PPO training. Loaded from config, never hardcoded."""

    # PPO hyperparameters
    learning_rate: float = Field(default=3e-4, gt=0)
    n_steps: int = Field(default=2048, gt=0, description="Steps per rollout")
    batch_size: int = Field(default=64, gt=0)
    n_epochs: int = Field(default=10, gt=0, description="Epochs per update")
    gamma: float = Field(default=0.95, ge=0, le=1, description="Discount factor")
    gae_lambda: float = Field(default=0.95, ge=0, le=1)
    clip_range: float = Field(default=0.2, gt=0)
    ent_coef: float = Field(default=0.01, ge=0, description="Entropy coefficient")
    vf_coef: float = Field(default=0.5, gt=0, description="Value function coefficient")
    max_grad_norm: float = Field(default=0.5, gt=0)

    # Training schedule
    total_timesteps: int = Field(default=500_000, gt=0)
    log_interval: int = Field(default=10, gt=0)

    # Network architecture
    net_arch_pi: list[int] = Field(default=[128, 128], description="Policy network layers")
    net_arch_vf: list[int] = Field(default=[128, 128], description="Value network layers")

    # Environment
    facility_config: FacilityConfig = Field(default_factory=FacilityConfig)
    max_patients: int = Field(default=20, gt=0)

    # Output
    save_path: str = Field(default="models/ppo_cart")
    seed: int = Field(default=42)


# ---------------------------------------------------------------------------
# Training callback for metrics logging
# ---------------------------------------------------------------------------

@dataclass
class TrainingMetrics:
    """Collected during training for analysis."""

    episode_rewards: list[float] = field(default_factory=list)
    episode_lengths: list[float] = field(default_factory=list)
    infusions: list[int] = field(default_factory=list)
    failures: list[int] = field(default_factory=list)


class MetricsCallback(BaseCallback):
    """Logs episode-level metrics during training."""

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
        self.metrics = TrainingMetrics()

    def _on_step(self) -> bool:
        # Check for completed episodes in the info buffer
        for info in self.locals.get("infos", []):
            if "episode" in info:
                self.metrics.episode_rewards.append(info["episode"]["r"])
                self.metrics.episode_lengths.append(info["episode"]["l"])
            if "total_infusions" in info:
                self.metrics.infusions.append(info["total_infusions"])
            if "total_failures" in info:
                self.metrics.failures.append(info["total_failures"])
        return True


# ---------------------------------------------------------------------------
# Agent wrapper
# ---------------------------------------------------------------------------

class PPOSchedulingAgent:
    """PPO agent for CAR-T manufacturing scheduling.

    Wraps SB3 PPO with training, evaluation, and persistence.

    Usage::

        agent = PPOSchedulingAgent(TrainingConfig(total_timesteps=100_000))
        metrics = agent.train()
        agent.save("models/ppo_v1")

        # Later:
        agent = PPOSchedulingAgent.load("models/ppo_v1")
        results = agent.evaluate(n_episodes=100)
    """

    def __init__(self, config: TrainingConfig | None = None) -> None:
        self.config = config or TrainingConfig()
        self._env: CARTSchedulingEnv | None = None
        self._model: MaskablePPO | None = None

    def train(self) -> TrainingMetrics:
        """Train the MaskablePPO agent. Returns training metrics."""
        self._env = self._make_env()
        callback = MetricsCallback()

        self._model = MaskablePPO(
            policy="MlpPolicy",
            env=self._env,
            learning_rate=self.config.learning_rate,
            n_steps=self.config.n_steps,
            batch_size=self.config.batch_size,
            n_epochs=self.config.n_epochs,
            gamma=self.config.gamma,
            gae_lambda=self.config.gae_lambda,
            clip_range=self.config.clip_range,
            ent_coef=self.config.ent_coef,
            vf_coef=self.config.vf_coef,
            max_grad_norm=self.config.max_grad_norm,
            policy_kwargs={
                "net_arch": {
                    "pi": list(self.config.net_arch_pi),
                    "vf": list(self.config.net_arch_vf),
                }
            },
            seed=self.config.seed,
            verbose=1,
        )

        self._model.learn(
            total_timesteps=self.config.total_timesteps,
            callback=callback,
            log_interval=self.config.log_interval,
        )

        return callback.metrics

    def predict(
        self,
        obs: np.ndarray,
        deterministic: bool = True,
        action_masks: np.ndarray | None = None,
    ) -> int:
        """Get action for a single observation."""
        assert self._model is not None, "Model not trained or loaded"
        action, _ = self._model.predict(
            obs, deterministic=deterministic, action_masks=action_masks
        )
        return int(action)

    def evaluate(
        self,
        n_episodes: int = 100,
        seed: int | None = None,
        facility_config: FacilityConfig | None = None,
    ) -> EvaluationResults:
        """Evaluate the trained agent over multiple episodes."""
        assert self._model is not None, "Model not trained or loaded"

        fc = facility_config or self.config.facility_config
        base_seed = seed if seed is not None else self.config.seed

        episode_rewards: list[float] = []
        episode_infusions: list[int] = []
        episode_failures: list[int] = []
        episode_queue_sizes: list[int] = []

        for i in range(n_episodes):
            ep_config = FacilityConfig(**{**fc.model_dump(), "seed": base_seed + i})
            env = CARTSchedulingEnv(ep_config, max_patients=self.config.max_patients)
            obs, _ = env.reset()
            total_reward = 0.0
            done = False

            while not done:
                action = self.predict(obs, action_masks=env.action_masks())
                obs, reward, done, _, info = env.step(action)
                total_reward += reward

            episode_rewards.append(total_reward)
            episode_infusions.append(info.get("total_infusions", 0))
            episode_failures.append(info.get("total_failures", 0))
            episode_queue_sizes.append(info["state"].num_patients_waiting)

        return EvaluationResults(
            n_episodes=n_episodes,
            mean_reward=float(np.mean(episode_rewards)),
            std_reward=float(np.std(episode_rewards)),
            mean_infusions=float(np.mean(episode_infusions)),
            std_infusions=float(np.std(episode_infusions)),
            mean_failures=float(np.mean(episode_failures)),
            mean_queue_size=float(np.mean(episode_queue_sizes)),
            all_rewards=episode_rewards,
            all_infusions=episode_infusions,
            all_failures=episode_failures,
        )

    def save(self, path: str | Path) -> None:
        """Save model and config to disk."""
        assert self._model is not None, "Model not trained or loaded"
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        self._model.save(str(path / "policy"))
        (path / "config.json").write_text(self.config.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: str | Path) -> PPOSchedulingAgent:
        """Load a saved agent from disk."""
        path = Path(path)
        config = TrainingConfig.model_validate_json((path / "config.json").read_text())

        agent = cls(config)
        agent._env = agent._make_env()
        agent._model = MaskablePPO.load(str(path / "policy"), env=agent._env)
        return agent

    def _make_env(self) -> CARTSchedulingEnv:
        """Create the Gymnasium environment from config."""
        return CARTSchedulingEnv(
            config=self.config.facility_config,
            max_patients=self.config.max_patients,
        )


# ---------------------------------------------------------------------------
# Evaluation results
# ---------------------------------------------------------------------------

@dataclass
class EvaluationResults:
    """Results from evaluating an agent or heuristic."""

    n_episodes: int
    mean_reward: float
    std_reward: float
    mean_infusions: float
    std_infusions: float
    mean_failures: float
    mean_queue_size: float
    all_rewards: list[float] = field(default_factory=list)
    all_infusions: list[int] = field(default_factory=list)
    all_failures: list[int] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "n_episodes": self.n_episodes,
            "mean_reward": round(self.mean_reward, 1),
            "std_reward": round(self.std_reward, 1),
            "mean_infusions": round(self.mean_infusions, 1),
            "std_infusions": round(self.std_infusions, 1),
            "mean_failures": round(self.mean_failures, 1),
            "mean_queue_size": round(self.mean_queue_size, 1),
        }

    def __str__(self) -> str:
        return (
            f"EvaluationResults(n={self.n_episodes}, "
            f"reward={self.mean_reward:.1f}±{self.std_reward:.1f}, "
            f"infusions={self.mean_infusions:.1f}±{self.std_infusions:.1f}, "
            f"failures={self.mean_failures:.1f}, "
            f"queue={self.mean_queue_size:.1f})"
        )
