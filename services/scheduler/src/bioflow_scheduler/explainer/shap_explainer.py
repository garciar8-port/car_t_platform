"""SHAP-based explainability for CAR-T scheduling recommendations.

Provides feature-level attributions for every scheduling decision,
mapping raw observation features to clinical language that coordinators
and regulatory reviewers can understand.

Architectural requirement: explainability is computed alongside every
recommendation, not as a separate job (see PROJECT_CONTEXT.md).
"""

from __future__ import annotations

import time
from typing import Literal

import numpy as np
import shap
from pydantic import BaseModel, Field

from bioflow_scheduler.simulator.gymnasium_env import (
    CLOCK_FEATURES,
    INVENTORY_FEATURES,
    PATIENT_FEATURES,
    SUITE_FEATURES,
    CARTSchedulingEnv,
    _PHASE_ORDER,
    _STATUS_ORDER,
)


# ---------------------------------------------------------------------------
# Feature name registry — maps vector indices to human-readable names
# ---------------------------------------------------------------------------

# Clinical-friendly labels for observation features
_SUITE_STATUS_NAMES = [f"status_{s.value}" for s in _STATUS_ORDER]
_SUITE_PHASE_NAMES = [f"phase_{p.value}" for p in _PHASE_ORDER]
_SUITE_NUMERIC_NAMES = ["days_remaining", "days_remaining_variance", "occupied"]

_PATIENT_FEATURE_NAMES = [
    "clinical_urgency",
    "days_since_leukapheresis",
    "product_shelf_life",
    "cells_collected",
    "indication",
]

_INVENTORY_NAMES = ["media_supply", "viral_vector_supply", "reagent_supply"]
_CLOCK_NAMES = ["day_of_week", "hour_of_day"]

# Mapping from feature name patterns to plain-english templates
_CLINICAL_TEMPLATES: dict[str, str] = {
    "clinical_urgency": "Patient {idx} has {level} clinical urgency ({val:.2f})",
    "days_since_leukapheresis": "Patient {idx} has waited {val:.0f} days (normalized) since leukapheresis",
    "product_shelf_life": "Patient {idx} has {level} remaining product shelf life ({val:.2f})",
    "cells_collected": "Patient {idx} {'has' if val > 0.5 else 'has not'} had cells collected",
    "indication": "Patient {idx} indication type ({val:.2f})",
    "status_idle": "Suite {idx} is idle",
    "status_in_use": "Suite {idx} is in use",
    "days_remaining": "Suite {idx} has {val:.1f} days remaining (normalized)",
    "media_supply": "Media supply level ({val:.2f})",
    "viral_vector_supply": "Viral vector supply level ({val:.2f})",
    "reagent_supply": "Reagent supply level ({val:.2f})",
    "day_of_week": "Day of week ({val:.2f})",
    "hour_of_day": "Hour of day ({val:.2f})",
}


def build_feature_names(num_suites: int, max_patients: int) -> list[str]:
    """Generate human-readable feature names matching the observation vector layout."""
    names: list[str] = []

    for s in range(num_suites):
        prefix = f"suite_{s + 1}"
        for n in _SUITE_STATUS_NAMES:
            names.append(f"{prefix}_{n}")
        for n in _SUITE_PHASE_NAMES:
            names.append(f"{prefix}_{n}")
        for n in _SUITE_NUMERIC_NAMES:
            names.append(f"{prefix}_{n}")

    for p in range(max_patients):
        prefix = f"patient_{p + 1}"
        for n in _PATIENT_FEATURE_NAMES:
            names.append(f"{prefix}_{n}")

    names.extend(_INVENTORY_NAMES)
    names.extend(_CLOCK_NAMES)

    return names


def _plain_english(feature_name: str, feature_value: float, shap_value: float) -> str:
    """Generate a clinical-language explanation for a feature attribution."""
    # Extract entity index if present
    parts = feature_name.split("_")
    idx = ""
    base_name = feature_name
    for i, part in enumerate(parts):
        if part.isdigit():
            idx = part
            base_name = "_".join(parts[i + 1:])
            break

    direction = "favoring" if shap_value > 0 else "against"
    level = "high" if feature_value > 0.6 else "moderate" if feature_value > 0.3 else "low"

    # Try to match a clinical template
    if "clinical_urgency" in feature_name:
        return f"Patient {idx} has {level} clinical urgency ({feature_value:.2f}), {direction} assignment"
    if "days_since_leukapheresis" in feature_name:
        return f"Patient {idx} wait time ({feature_value:.2f} normalized), {direction} assignment"
    if "product_shelf_life" in feature_name:
        return f"Patient {idx} has {level} remaining product shelf life ({feature_value:.2f}), {direction} assignment"
    if "cells_collected" in feature_name:
        status = "collected" if feature_value > 0.5 else "not yet collected"
        return f"Patient {idx} cells {status}, {direction} assignment"
    if "status_idle" in feature_name:
        return f"Suite {idx} is {'idle' if feature_value > 0.5 else 'occupied'}, {direction} assignment"
    if "status_in_use" in feature_name:
        return f"Suite {idx} is {'in use' if feature_value > 0.5 else 'not in use'}, {direction} assignment"
    if "days_remaining" in feature_name and "variance" not in feature_name:
        return f"Suite {idx} has {feature_value:.2f} days remaining (normalized), {direction} assignment"
    if "media_supply" in feature_name:
        return f"Media supply at {level} level ({feature_value:.2f}), {direction} assignment"
    if "viral_vector" in feature_name:
        return f"Viral vector supply at {level} level ({feature_value:.2f}), {direction} assignment"
    if "reagent" in feature_name:
        return f"Reagent supply at {level} level ({feature_value:.2f}), {direction} assignment"

    return f"{feature_name}={feature_value:.2f}, {direction} assignment (SHAP={shap_value:+.3f})"


# ---------------------------------------------------------------------------
# Explanation result schemas
# ---------------------------------------------------------------------------

class ExplanationFactor(BaseModel):
    """A single feature's contribution to the recommendation."""

    feature_name: str
    feature_value: float
    shap_value: float
    direction: Literal["increases_priority", "decreases_priority"]
    plain_english: str


class ExplanationResult(BaseModel):
    """Complete explanation for a single scheduling recommendation."""

    shap_values: list[float]
    feature_names: list[str]
    top_factors: list[ExplanationFactor] = Field(default_factory=list)
    recommended_action: int = 0
    computation_time_ms: float = 0.0

    def summary(self) -> str:
        """Human-readable summary of the top factors."""
        lines = [f"Action: {self.recommended_action} ({self.computation_time_ms:.0f}ms)"]
        for f in self.top_factors:
            sign = "+" if f.shap_value > 0 else ""
            lines.append(f"  {sign}{f.shap_value:.3f}  {f.plain_english}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# SHAP Explainer
# ---------------------------------------------------------------------------

class SHAPExplainer:
    """Computes SHAP feature attributions for PPO scheduling decisions.

    Uses KernelExplainer (model-agnostic) with a background dataset
    collected from the agent's own rollouts.

    Usage::

        explainer = SHAPExplainer(agent, n_background=100)
        action, explanation = explainer.explain(obs, action_masks)
    """

    def __init__(
        self,
        agent,  # PPOSchedulingAgent — avoid circular import
        n_background: int = 100,
        n_samples: int = 50,
        top_k: int = 5,
        seed: int = 42,
    ) -> None:
        self._agent = agent
        self._n_samples = n_samples
        self._top_k = top_k

        config = agent.config
        self._feature_names = build_feature_names(
            num_suites=config.facility_config.num_suites,
            max_patients=config.max_patients,
        )

        # Collect background observations
        self._background = self._collect_background(n_background, seed)

        # Initialize SHAP explainer with the policy's value function
        self._explainer = shap.KernelExplainer(
            self._model_fn,
            self._background,
        )

    def explain(
        self,
        obs: np.ndarray,
        action_masks: np.ndarray | None = None,
    ) -> tuple[int, ExplanationResult]:
        """Get action and SHAP explanation for a single observation."""
        start = time.perf_counter()

        action = self._agent.predict(obs, action_masks=action_masks)

        shap_values = self._explainer.shap_values(
            obs.reshape(1, -1),
            nsamples=self._n_samples,
            silent=True,
        )

        # shap_values shape: (1, n_features) for single output
        if isinstance(shap_values, list):
            sv = np.array(shap_values[0]).flatten()
        else:
            sv = np.array(shap_values).flatten()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Build top factors
        top_indices = np.argsort(np.abs(sv))[::-1][: self._top_k]
        top_factors = []
        for idx in top_indices:
            feat_name = self._feature_names[idx]
            feat_val = float(obs[idx])
            shap_val = float(sv[idx])
            top_factors.append(
                ExplanationFactor(
                    feature_name=feat_name,
                    feature_value=feat_val,
                    shap_value=shap_val,
                    direction="increases_priority" if shap_val > 0 else "decreases_priority",
                    plain_english=_plain_english(feat_name, feat_val, shap_val),
                )
            )

        return action, ExplanationResult(
            shap_values=[float(v) for v in sv],
            feature_names=self._feature_names,
            top_factors=top_factors,
            recommended_action=action,
            computation_time_ms=elapsed_ms,
        )

    def _model_fn(self, X: np.ndarray) -> np.ndarray:
        """Wraps the PPO value function for SHAP."""
        import torch

        model = self._agent._model
        obs_tensor = torch.as_tensor(X, dtype=torch.float32)
        with torch.no_grad():
            values = model.policy.predict_values(obs_tensor)
        return values.numpy().flatten()

    def _collect_background(self, n: int, seed: int) -> np.ndarray:
        """Run the agent for n steps to collect representative observations."""
        from bioflow_scheduler.mdp.schemas import FacilityConfig

        config = self._agent.config
        fc = FacilityConfig(**{**config.facility_config.model_dump(), "seed": seed})
        env = CARTSchedulingEnv(fc, max_patients=config.max_patients)

        observations = []
        obs, _ = env.reset()
        for _ in range(n):
            observations.append(obs.copy())
            masks = env.action_masks()
            action = self._agent.predict(obs, action_masks=masks)
            obs, _, done, _, _ = env.step(action)
            if done:
                obs, _ = env.reset()

        return np.array(observations)
