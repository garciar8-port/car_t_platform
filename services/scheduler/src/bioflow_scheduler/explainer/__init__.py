"""SHAP-based explainability for scheduling recommendations."""

from bioflow_scheduler.explainer.shap_explainer import (
    ExplanationFactor,
    ExplanationResult,
    SHAPExplainer,
    build_feature_names,
)

__all__ = [
    "ExplanationFactor",
    "ExplanationResult",
    "SHAPExplainer",
    "build_feature_names",
]
