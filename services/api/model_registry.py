"""
MLflow model registry for tracking trained scheduling models.

Tracks model versions, training metrics, hyperparameters, and artifacts.
Supports model promotion (staging → production) for safe deployments.
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional

# MLflow is optional — gracefully degrade if not installed
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///./mlflow.db")
MODEL_NAME = "bioflow-scheduler"


class ModelInfo(BaseModel):
    version: str
    stage: str  # staging, production, archived
    run_id: Optional[str] = None
    metrics: dict = {}
    parameters: dict = {}
    registered_at: Optional[str] = None
    description: str = ""


class ModelRegistry:
    def __init__(self):
        if MLFLOW_AVAILABLE:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            self.client = MlflowClient()
        else:
            self.client = None
        self._local_versions: list[ModelInfo] = []

    def register_model(
        self,
        model_path: str,
        metrics: dict,
        parameters: dict,
        description: str = "",
    ) -> ModelInfo:
        """Register a trained model with its metrics and parameters."""
        version = f"v{len(self._local_versions) + 1}.0.0"

        if self.client and MLFLOW_AVAILABLE:
            with mlflow.start_run() as run:
                mlflow.log_params(parameters)
                mlflow.log_metrics(metrics)
                mlflow.log_artifact(model_path)
                mlflow.set_tag("model_type", "MaskablePPO")
                mlflow.set_tag("framework", "stable-baselines3")

                # Register model
                model_uri = f"runs:/{run.info.run_id}/model"
                result = mlflow.register_model(model_uri, MODEL_NAME)
                version = f"v{result.version}.0.0"

                info = ModelInfo(
                    version=version,
                    stage="staging",
                    run_id=run.info.run_id,
                    metrics=metrics,
                    parameters=parameters,
                    registered_at=datetime.now(timezone.utc).isoformat(),
                    description=description,
                )
        else:
            info = ModelInfo(
                version=version,
                stage="staging",
                metrics=metrics,
                parameters=parameters,
                registered_at=datetime.now(timezone.utc).isoformat(),
                description=description,
            )

        self._local_versions.append(info)
        return info

    def promote_to_production(self, version: str) -> ModelInfo:
        """Promote a model version from staging to production."""
        for m in self._local_versions:
            if m.version == version:
                m.stage = "production"
                return m
        raise ValueError(f"Model version {version} not found")

    def get_production_model(self) -> Optional[ModelInfo]:
        """Get the current production model."""
        for m in reversed(self._local_versions):
            if m.stage == "production":
                return m
        return None

    def list_models(self) -> list[ModelInfo]:
        """List all registered model versions."""
        return self._local_versions

    def get_current_info(self) -> ModelInfo:
        """Get info about the currently loaded model (even without MLflow)."""
        prod = self.get_production_model()
        if prod:
            return prod
        # Return default for the phase4 model
        return ModelInfo(
            version="v0.4.0-phase4",
            stage="production",
            metrics={
                "mean_reward": 1091.0,
                "mean_infusions": 16.2,
                "mean_wait_days": 8.3,
                "mean_utilization": 0.81,
            },
            parameters={
                "algorithm": "MaskablePPO",
                "timesteps": 500000,
                "learning_rate": 0.0003,
                "n_steps": 2048,
                "acuity_exponent": 2.0,
            },
            registered_at="2026-04-08T00:00:00Z",
            description="Phase 4: Acuity-weighted rewards + SHAP explainability",
        )


# Singleton
registry = ModelRegistry()
