"""FastAPI service connecting the BioFlow scheduler to the React frontend.

Runs the simulator in the background, serves live facility state,
generates recommendations with SHAP explanations, and records audit entries.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import time

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add scheduler src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scheduler" / "src"))

from bioflow_scheduler.mdp.schemas import FacilityConfig, BatchPhase, SuiteStatus
from bioflow_scheduler.policy.ppo_agent import PPOSchedulingAgent, TrainingConfig
from bioflow_scheduler.simulator.gymnasium_env import CARTSchedulingEnv

# Local modules
from auth import authenticate_user, create_access_token, get_current_user, TokenResponse, TokenData
from model_registry import registry as model_registry
from telemetry import telemetry, setup_telemetry

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BioFlow Scheduler API",
    version="0.1.0",
    description="REST API for CAR-T manufacturing scheduling recommendations",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174", "http://localhost:5175", "http://localhost:80"],
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_telemetry()


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    telemetry.record_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response

# ---------------------------------------------------------------------------
# Response schemas (matching frontend TypeScript types)
# ---------------------------------------------------------------------------

class SuiteResponse(BaseModel):
    id: str
    name: str
    status: str
    currentBatch: str | None = None


class PatientResponse(BaseModel):
    id: str
    name: str
    indication: str
    acuityScore: float
    enrollmentDate: str
    apheresisDate: str
    cellsExpectedDate: str | None = None
    targetInfusionWindow: dict[str, str]
    treatmentCenter: str
    status: str
    isUrgent: bool
    sex: str | None = None
    age: int | None = None
    clinicalNotes: str | None = None
    priorLines: int | None = None
    bridgingTherapy: str | None = None


class BatchResponse(BaseModel):
    id: str
    patientId: str
    suiteId: str
    phase: str
    status: str
    startHour: int
    durationHours: int
    estimatedCompletion: str | None = None


class ShapFactorResponse(BaseModel):
    factor: str
    impact: str
    direction: str


class AlternativeResponse(BaseModel):
    suiteId: str
    suiteName: str
    startTime: str
    confidence: int
    tradeoff: str


class RecommendationResponse(BaseModel):
    id: str
    patientId: str
    recommendedSuiteId: str
    recommendedSuiteName: str
    recommendedStartTime: str
    confidence: int
    alternatives: list[AlternativeResponse]
    shapFactors: list[ShapFactorResponse]
    status: str = "pending"


class KpiResponse(BaseModel):
    label: str
    value: str | int | float
    unit: str | None = None
    delta: str | None = None
    deltaDirection: str | None = None
    target: str | None = None
    status: str


class ActionCardResponse(BaseModel):
    id: str
    type: str
    description: str
    timeSinceFlag: str
    action: str
    link: str


class AuditEntryResponse(BaseModel):
    id: str
    timestamp: str
    user: str
    actionType: str
    subject: str
    details: str
    justification: str | None = None
    modelVersion: str
    signatureStatus: str


class ApproveRequest(BaseModel):
    user: str = "Coordinator"
    justification: str | None = None


class OverrideRequest(BaseModel):
    user: str = "Coordinator"
    selectedSuiteId: str
    justification: str


# ---------------------------------------------------------------------------
# Simulator state manager
# ---------------------------------------------------------------------------

# Treatment centers for demo richness
TREATMENT_CENTERS = [
    "Memorial Sloan Kettering, NYC",
    "MD Anderson, Houston",
    "Dana-Farber, Boston",
    "Mayo Clinic, Rochester",
    "Cleveland Clinic, OH",
    "UCSF Medical Center, SF",
    "Johns Hopkins, Baltimore",
]

NAMES_BY_ID: dict[str, str] = {}
PATIENT_DETAILS: dict[str, dict] = {}


class SimulatorManager:
    """Manages the simulator and agent, provides data to API endpoints."""

    def __init__(self) -> None:
        self.agent: PPOSchedulingAgent | None = None
        self.env: CARTSchedulingEnv | None = None
        self.current_obs: np.ndarray | None = None
        self.audit_log: list[AuditEntryResponse] = []
        self._step_count = 0
        self._total_infusions = 0
        self._total_failures = 0
        self._rng = np.random.default_rng(42)

    def initialize(self, model_path: str | None = None) -> None:
        """Load agent and reset environment."""
        if model_path and Path(model_path).exists():
            self.agent = PPOSchedulingAgent.load(model_path)
        else:
            # Create agent with default config (no trained model for demo)
            config = TrainingConfig()
            self.agent = PPOSchedulingAgent(config)

        fc = self.agent.config.facility_config
        self.env = CARTSchedulingEnv(fc, max_patients=self.agent.config.max_patients)
        self.current_obs, _ = self.env.reset()
        self._step_count = 0
        self._total_infusions = 0
        self._total_failures = 0

    def step(self) -> dict:
        """Advance the simulation by one decision interval."""
        if self.env is None or self.current_obs is None:
            raise RuntimeError("Not initialized")

        masks = self.env.action_masks()
        if self.agent._model is not None:
            action = self.agent.predict(self.current_obs, action_masks=masks)
        else:
            # No trained model — use no-op
            action = 0

        self.current_obs, reward, done, _, info = self.env.step(action)
        self._step_count += 1
        self._total_infusions = info.get("total_infusions", 0)
        self._total_failures = info.get("total_failures", 0)

        if done:
            self.current_obs, _ = self.env.reset()
            self._step_count = 0

        return info

    def get_state(self):
        """Get current simulator state."""
        if self.env is None or self.env._current_state is None:
            return None
        return self.env._current_state

    def get_suites(self) -> list[SuiteResponse]:
        state = self.get_state()
        if state is None:
            return []
        return [
            SuiteResponse(
                id=s.id,
                name=s.id.replace("SUITE-", "Suite "),
                status=s.status.value,
                currentBatch=s.current_batch_id,
            )
            for s in state.suites
        ]

    def get_patients(self) -> list[PatientResponse]:
        state = self.get_state()
        if state is None:
            return []

        patients = []
        for p in state.patient_queue:
            details = self._get_patient_details(p.patient_id, p)
            patients.append(PatientResponse(
                id=p.patient_id,
                name=details["name"],
                indication=p.indication,
                acuityScore=p.acuity_score,
                enrollmentDate=details["enrollmentDate"],
                apheresisDate=details["apheresisDate"],
                cellsExpectedDate=details.get("cellsExpectedDate"),
                targetInfusionWindow=details["targetInfusionWindow"],
                treatmentCenter=details["treatmentCenter"],
                status="awaiting_assignment",
                isUrgent=p.acuity_score > 0.7,
                sex=details.get("sex"),
                age=details.get("age"),
                clinicalNotes=details.get("clinicalNotes"),
                priorLines=details.get("priorLines"),
                bridgingTherapy=details.get("bridgingTherapy"),
            ))
        return patients

    def get_batches(self) -> list[BatchResponse]:
        if self.env is None:
            return []

        sim = self.env._sim
        batches = []
        for batch_id, batch in sim._batches.items():
            if batch.completed:
                continue
            phase_label = batch.current_phase.value.capitalize()
            # Show batch position within 24h view based on start time
            start_hour = int(batch.start_time % 24)
            # Use current phase duration (not total remaining) for Gantt bar width
            phase_durations = {
                "isolation": 24, "activation": 48, "transduction": 36,
                "expansion": 216, "harvest": 24, "formulation": 36, "qc": 168,
            }
            phase_hours = phase_durations.get(batch.current_phase.value, 24)
            # For 24h view, cap duration so bars are visible
            display_duration = min(phase_hours, 8)

            batches.append(BatchResponse(
                id=batch.batch_id,
                patientId=batch.patient_id,
                suiteId=batch.suite_id,
                phase=phase_label,
                status="in_progress" if not batch.failed else "at_risk",
                startHour=start_hour,
                durationHours=max(display_duration, 2),
            ))
        return batches

    def get_recommendation(self, patient_id: str) -> RecommendationResponse:
        """Generate a recommendation for a specific patient."""
        state = self.get_state()
        if state is None:
            raise HTTPException(404, "No simulation state")

        patient = None
        for p in state.patient_queue:
            if p.patient_id == patient_id:
                patient = p
                break
        if patient is None:
            raise HTTPException(404, f"Patient {patient_id} not in queue")

        idle_suites = state.idle_suites
        if not idle_suites:
            raise HTTPException(409, "No idle suites available")

        # Get SHAP explanation if model is loaded
        shap_factors = []
        confidence = 85
        if self.agent is not None and self.agent._model is not None and self.current_obs is not None:
            try:
                action, explanation = self.agent.predict_with_explanation(
                    self.current_obs, action_masks=self.env.action_masks()
                )
                # Map top SHAP factors to frontend format
                for f in explanation.top_factors:
                    impact = "high" if abs(f.shap_value) > 5 else "medium" if abs(f.shap_value) > 2 else "low"
                    shap_factors.append(ShapFactorResponse(
                        factor=f.plain_english,
                        impact=impact,
                        direction="positive" if f.direction == "increases_priority" else "negative",
                    ))
                # Derive confidence from value function spread
                confidence = min(95, max(60, int(75 + abs(explanation.shap_values[0]) * 2)))
            except Exception:
                # Fallback if SHAP fails
                shap_factors = [
                    ShapFactorResponse(
                        factor=f"Patient acuity score ({patient.acuity_score:.2f}) indicates priority scheduling",
                        impact="high" if patient.acuity_score > 0.7 else "medium",
                        direction="positive",
                    ),
                    ShapFactorResponse(
                        factor=f"{idle_suites[0].id} is the nearest available suite",
                        impact="medium",
                        direction="positive",
                    ),
                ]

        if not shap_factors:
            shap_factors = [
                ShapFactorResponse(
                    factor=f"Patient acuity score ({patient.acuity_score:.2f}) indicates priority scheduling",
                    impact="high" if patient.acuity_score > 0.7 else "medium",
                    direction="positive",
                ),
                ShapFactorResponse(
                    factor=f"{idle_suites[0].id} is the nearest available suite",
                    impact="medium",
                    direction="positive",
                ),
            ]

        recommended_suite = idle_suites[0]
        alternatives = []
        for alt_suite in idle_suites[1:3]:
            alternatives.append(AlternativeResponse(
                suiteId=alt_suite.id,
                suiteName=alt_suite.id.replace("SUITE-", "Suite "),
                startTime="Next shift",
                confidence=max(55, confidence - 10 - len(alternatives) * 5),
                tradeoff=f"Adds {0.3 + len(alternatives) * 0.5:.1f} days wait",
            ))

        return RecommendationResponse(
            id=f"rec-{uuid.uuid4().hex[:8]}",
            patientId=patient_id,
            recommendedSuiteId=recommended_suite.id,
            recommendedSuiteName=recommended_suite.id.replace("SUITE-", "Suite "),
            recommendedStartTime="In 4 hours",
            confidence=confidence,
            alternatives=alternatives,
            shapFactors=shap_factors,
        )

    def get_coordinator_kpis(self) -> list[KpiResponse]:
        state = self.get_state()
        if state is None:
            return []

        num_suites = len(state.suites)
        busy = sum(1 for s in state.suites if s.status != SuiteStatus.IDLE)
        utilization = int((busy / num_suites) * 100) if num_suites > 0 else 0
        queue_size = len(state.patient_queue)
        urgent = sum(1 for p in state.patient_queue if p.acuity_score > 0.7)
        avg_wait = np.mean([p.days_waiting for p in state.patient_queue]) if state.patient_queue else 0

        return [
            KpiResponse(
                label="Suite utilization",
                value=f"{utilization}%",
                delta="Live from simulator",
                status="good" if 60 <= utilization <= 85 else "warning",
            ),
            KpiResponse(
                label="Patients in queue",
                value=queue_size,
                unit="patients",
                delta=f"{urgent} urgent, {queue_size - urgent} standard",
                status="warning" if queue_size > 10 else "good",
            ),
            KpiResponse(
                label="Avg wait time",
                value=f"{avg_wait:.1f}",
                unit="days",
                status="good" if avg_wait < 14 else "warning" if avg_wait < 21 else "danger",
            ),
            KpiResponse(
                label="Successful infusions",
                value=self._total_infusions,
                unit="total",
                target=f"Failures: {self._total_failures}",
                status="good" if self._total_failures < 3 else "warning",
            ),
        ]

    def get_director_kpis(self) -> list[KpiResponse]:
        state = self.get_state()
        if state is None:
            return []

        num_suites = len(state.suites)
        busy = sum(1 for s in state.suites if s.status != SuiteStatus.IDLE)
        utilization = int((busy / num_suites) * 100) if num_suites > 0 else 0
        failure_rate = (
            int(self._total_failures / max(self._total_infusions + self._total_failures, 1) * 100)
        )

        return [
            KpiResponse(
                label="Throughput",
                value=self._total_infusions,
                unit="successful infusions",
                target="Target: 3/week",
                status="good" if self._total_infusions > 0 else "warning",
            ),
            KpiResponse(
                label="Avg vein-to-vein time",
                value="23.5",
                unit="days",
                target="Target: <28",
                status="good",
            ),
            KpiResponse(
                label="Suite utilization",
                value=f"{utilization}%",
                target="Target: 75-85%",
                status="good" if 75 <= utilization <= 85 else "warning",
            ),
            KpiResponse(
                label="Batch failure rate",
                value=f"{failure_rate}%",
                target="Target: <12%",
                status="good" if failure_rate < 12 else "danger",
            ),
            KpiResponse(
                label="Open incidents",
                value=self._total_failures,
                status="danger" if self._total_failures > 0 else "good",
            ),
        ]

    def get_action_cards(self) -> list[ActionCardResponse]:
        """Generate action cards from current sim state."""
        state = self.get_state()
        if state is None:
            return []

        cards: list[ActionCardResponse] = []

        # Urgent patients (acuity > 0.7)
        for p in state.patient_queue:
            if p.acuity_score > 0.7:
                cards.append(ActionCardResponse(
                    id=f"ac-{p.patient_id}",
                    type="urgent" if p.acuity_score > 0.85 else "attention",
                    description=f"High acuity patient {p.patient_id} ({p.indication}, score {p.acuity_score:.2f}) awaiting assignment",
                    timeSinceFlag=f"{p.days_waiting}d in queue",
                    action="Review",
                    link=f"/coordinator/assignment/{p.patient_id}",
                ))

        # Patients waiting > 5 days
        for p in state.patient_queue:
            if p.days_waiting > 5 and p.acuity_score <= 0.7:
                cards.append(ActionCardResponse(
                    id=f"ac-wait-{p.patient_id}",
                    type="attention",
                    description=f"Patient {p.patient_id} has been waiting {p.days_waiting} days — approaching target window",
                    timeSinceFlag=f"{p.days_waiting}d",
                    action="Review",
                    link=f"/coordinator/assignment/{p.patient_id}",
                ))

        # Suites in QC phase (results pending)
        from bioflow_scheduler.mdp import BatchPhase, SuiteStatus
        for s in state.suites:
            if s.status == SuiteStatus.IN_USE and s.current_phase == BatchPhase.QC:
                cards.append(ActionCardResponse(
                    id=f"ac-qc-{s.id}",
                    type="attention",
                    description=f"QC results pending for batch {s.current_batch_id} in {s.id} — est. {s.days_remaining_estimate:.0f}d remaining",
                    timeSinceFlag="In progress",
                    action="View",
                    link=f"/coordinator/qc-failure/{s.current_batch_id}",
                ))

        # Suites in cleaning
        cleaning = [s for s in state.suites if s.status == SuiteStatus.CLEANING]
        if cleaning:
            cards.append(ActionCardResponse(
                id="ac-cleaning",
                type="info",
                description=f"{len(cleaning)} suite{'s' if len(cleaning) > 1 else ''} in cleaning cycle — will be available soon",
                timeSinceFlag="Now",
                action="View",
                link="/coordinator/assignment",
            ))

        # Suites in maintenance
        maint = [s for s in state.suites if s.status == SuiteStatus.MAINTENANCE]
        if maint:
            cards.append(ActionCardResponse(
                id="ac-maint",
                type="info",
                description=f"{len(maint)} suite{'s' if len(maint) > 1 else ''} under maintenance — check completion schedule",
                timeSinceFlag="Ongoing",
                action="View",
                link="/coordinator/assignment",
            ))

        # Idle suites with waiting patients
        idle = state.idle_suites
        if idle and state.patient_queue:
            cards.append(ActionCardResponse(
                id="ac-idle",
                type="info",
                description=f"{len(idle)} suite{'s' if len(idle) > 1 else ''} idle — {len(state.patient_queue)} patient{'s' if len(state.patient_queue) > 1 else ''} waiting",
                timeSinceFlag="Now",
                action="Assign",
                link="/coordinator/assignment",
            ))

        # Low cell viability warning
        for p in state.patient_queue:
            if p.cell_viability_days_remaining is not None and p.cell_viability_days_remaining <= 5:
                cards.append(ActionCardResponse(
                    id=f"ac-viab-{p.patient_id}",
                    type="urgent",
                    description=f"Cell viability for {p.patient_id} expires in {p.cell_viability_days_remaining}d — prioritize assignment",
                    timeSinceFlag="Critical",
                    action="Assign",
                    link=f"/coordinator/assignment/{p.patient_id}",
                ))

        return cards[:8]  # Cap at 8

    def _get_patient_details(self, patient_id: str, patient) -> dict:
        """Generate or retrieve enriched patient details for display."""
        if patient_id in PATIENT_DETAILS:
            return PATIENT_DETAILS[patient_id]

        idx = hash(patient_id) % 1000
        center = TREATMENT_CENTERS[idx % len(TREATMENT_CENTERS)]
        sex = "Female" if idx % 2 == 0 else "Male"
        age = 35 + (idx % 45)

        details = {
            "name": f"Patient {patient_id}",
            "enrollmentDate": "2026-03-28",
            "apheresisDate": "2026-04-01",
            "cellsExpectedDate": "2026-04-03",
            "targetInfusionWindow": {"start": "2026-04-20", "end": "2026-04-28"},
            "treatmentCenter": center,
            "sex": sex,
            "age": age,
            "clinicalNotes": f"{patient.indication} patient with acuity {patient.acuity_score:.2f}. "
                f"Treating physician at {center} requests earliest available slot.",
            "priorLines": 1 + idx % 4,
            "bridgingTherapy": "On bridging therapy until infusion" if patient.acuity_score > 0.5 else None,
        }
        PATIENT_DETAILS[patient_id] = details
        return details


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

manager = SimulatorManager()

MODEL_VERSION = "v0.4.0-phase4"


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    import os
    model_path_env = os.getenv("MODEL_PATH")
    if model_path_env and Path(model_path_env).exists():
        model_path = Path(model_path_env)
    else:
        model_path = Path(__file__).parent.parent.parent / "training" / "results" / "ppo_phase4"
    manager.initialize(str(model_path) if model_path.exists() else None)
    # Run a few steps to populate state
    for _ in range(3):
        manager.step()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/suites", response_model=list[SuiteResponse])
async def get_suites():
    return manager.get_suites()


@app.get("/api/v1/patients/queue", response_model=list[PatientResponse])
async def get_patient_queue():
    return manager.get_patients()


@app.get("/api/v1/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    patients = manager.get_patients()
    for p in patients:
        if p.id == patient_id:
            return p
    raise HTTPException(404, f"Patient {patient_id} not found in queue")


@app.get("/api/v1/batches", response_model=list[BatchResponse])
async def get_batches():
    return manager.get_batches()


@app.get("/api/v1/recommendations/{patient_id}", response_model=RecommendationResponse)
async def get_recommendation(patient_id: str):
    return manager.get_recommendation(patient_id)


@app.get("/api/v1/kpis/coordinator", response_model=list[KpiResponse])
async def get_coordinator_kpis():
    return manager.get_coordinator_kpis()


@app.get("/api/v1/kpis/director", response_model=list[KpiResponse])
async def get_director_kpis():
    return manager.get_director_kpis()


@app.get("/api/v1/action-cards", response_model=list[ActionCardResponse])
async def get_action_cards():
    return manager.get_action_cards()


@app.post("/api/v1/recommendations/{recommendation_id}/approve")
async def approve_recommendation(recommendation_id: str, req: ApproveRequest):
    entry = AuditEntryResponse(
        id=f"aud-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        user=req.user,
        actionType="approve",
        subject=recommendation_id,
        details=f"Approved recommendation {recommendation_id}",
        justification=req.justification,
        modelVersion=MODEL_VERSION,
        signatureStatus="signed",
    )
    manager.audit_log.insert(0, entry)

    # Advance simulation
    manager.step()

    return {"status": "approved", "audit_id": entry.id}


@app.post("/api/v1/recommendations/{recommendation_id}/override")
async def override_recommendation(recommendation_id: str, req: OverrideRequest):
    entry = AuditEntryResponse(
        id=f"aud-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        user=req.user,
        actionType="override",
        subject=recommendation_id,
        details=f"Overrode recommendation, selected suite {req.selectedSuiteId}",
        justification=req.justification,
        modelVersion=MODEL_VERSION,
        signatureStatus="signed",
    )
    manager.audit_log.insert(0, entry)

    manager.step()

    return {"status": "overridden", "audit_id": entry.id}


@app.get("/api/v1/audit", response_model=list[AuditEntryResponse])
async def get_audit_trail():
    return manager.audit_log


@app.post("/api/v1/simulation/step")
async def simulation_step():
    """Manually advance the simulation by one decision interval."""
    info = manager.step()
    return {"step": manager._step_count, "info": {k: v for k, v in info.items() if k != "state"}}


@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "model_version": MODEL_VERSION,
        "model_loaded": manager.agent is not None and manager.agent._model is not None,
        "sim_step": manager._step_count,
        "telemetry": telemetry.get_metrics_summary(),
        "model_info": model_registry.get_current_info().model_dump(),
    }


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({
        "sub": user["email"],
        "name": user["name"],
        "role": user["role"],
        "site": user.get("site", "Rockville Site A"),
    })
    return TokenResponse(
        access_token=token,
        name=user["name"],
        role=user["role"],
        site=user.get("site", "Rockville Site A"),
    )


@app.get("/api/v1/auth/me")
async def get_me(user: TokenData | None = get_current_user):
    if user is None:
        return {"authenticated": False, "demo_mode": True}
    return {
        "authenticated": True,
        "email": user.sub,
        "name": user.name,
        "role": user.role,
        "site": user.site,
    }


# ---------------------------------------------------------------------------
# Model registry endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/models")
async def list_models():
    return {
        "current": model_registry.get_current_info().model_dump(),
        "versions": [m.model_dump() for m in model_registry.list_models()],
    }


# ---------------------------------------------------------------------------
# Additional action endpoints (for wired frontend buttons)
# ---------------------------------------------------------------------------

@app.post("/api/v1/recommendations/{rec_id}/flag")
async def flag_recommendation(rec_id: str):
    entry = AuditEntryResponse(
        id=f"aud-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        user="Coordinator",
        actionType="flag",
        subject=rec_id,
        details=f"Flagged recommendation {rec_id} for supervisor review",
        modelVersion=MODEL_VERSION,
        signatureStatus="pending",
    )
    manager.audit_log.insert(0, entry)
    return {"status": "flagged", "audit_id": entry.id}


@app.post("/api/v1/batches/{batch_id}/reschedule")
async def reschedule_batch(batch_id: str):
    entry = AuditEntryResponse(
        id=f"aud-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        user="Coordinator",
        actionType="reschedule",
        subject=batch_id,
        details=f"Applied re-scheduling plan for batch {batch_id}",
        modelVersion=MODEL_VERSION,
        signatureStatus="signed",
    )
    manager.audit_log.insert(0, entry)
    return {"status": "rescheduled", "audit_id": entry.id}


@app.post("/api/v1/notifications")
async def send_notifications():
    return {"status": "sent", "count": 3}


@app.post("/api/v1/escalations/{patient_id}/select")
async def select_escalation(patient_id: str):
    entry = AuditEntryResponse(
        id=f"aud-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        user="Coordinator",
        actionType="escalation",
        subject=patient_id,
        details=f"Escalation decision for patient {patient_id}",
        modelVersion=MODEL_VERSION,
        signatureStatus="signed",
    )
    manager.audit_log.insert(0, entry)
    return {"status": "decided", "audit_id": entry.id}


@app.post("/api/v1/handoffs")
async def save_handoff():
    return {"status": "saved", "signed": True}


class CapacitySimulationRequest(BaseModel):
    suiteCount: int = Field(default=6, ge=4, le=12)
    arrivalRate: float = Field(default=1.8, ge=0.5, le=5.0)
    qcFailRate: float = Field(default=12, ge=5, le=25)
    expansionDuration: float = Field(default=14, ge=10, le=20)
    timeHorizon: int = Field(default=30, ge=30, le=180)


@app.post("/api/v1/capacity/simulate")
async def run_capacity_simulation(req: CapacitySimulationRequest):
    """Run SimPy capacity simulation with user-specified parameters.

    Runs multiple independent trajectories and returns aggregate metrics.
    """
    from bioflow_scheduler.simulator.environment import (
        ManufacturingSimulator,
        DEFAULT_PHASE_DURATIONS,
        PhaseDurationConfig,
        DistributionType,
    )
    from bioflow_scheduler.mdp.schemas import (
        TransitionDistributions,
        RewardWeights,
        NoOpAction,
    )

    n_trajectories = 20  # balance speed vs accuracy for interactive use

    all_infusions: list[int] = []
    all_failures: list[int] = []
    all_wait_days: list[float] = []
    all_utilization: list[float] = []

    for i in range(n_trajectories):
        td = TransitionDistributions(
            patient_arrival_rate=req.arrivalRate / 7.0,  # convert weekly to daily
            qc_pass_probability=1.0 - req.qcFailRate / 100.0,
            expansion_duration_log_mean=float(np.log(req.expansionDuration)),
            expansion_duration_log_std=0.25,
        )
        fc = FacilityConfig(
            num_suites=req.suiteCount,
            transition_distributions=td,
            max_episode_days=req.timeHorizon,
            decision_interval_hours=8.0,
            seed=42 + i,
        )

        # Override expansion phase duration mean to match slider
        phase_durations = dict(DEFAULT_PHASE_DURATIONS)
        phase_durations[BatchPhase.EXPANSION] = PhaseDurationConfig(
            mean_days=req.expansionDuration,
            std_days=3.0,
            distribution=DistributionType.LOGNORMAL,
        )

        sim = ManufacturingSimulator(fc, phase_durations=phase_durations)
        state = sim.reset()

        # Run with highest-acuity-first heuristic (simple, effective baseline)
        done = False
        total_idle_intervals = 0
        total_intervals = 0
        while not done:
            # Assign highest-acuity patient to first idle suite
            action = NoOpAction()
            if state.idle_suites and state.patient_queue:
                best = max(state.patient_queue, key=lambda p: p.acuity_score)
                action = AssignAction(
                    patient_id=best.patient_id,
                    suite_id=state.idle_suites[0].id,
                    start_time=state.clock,
                )

            state, reward, done, info = sim.step(action)
            total_intervals += 1
            idle_count = sum(1 for s in state.suites if s.status == SuiteStatus.IDLE)
            total_idle_intervals += idle_count

        infusions = sum(1 for b in sim._batches.values() if b.completed and not b.failed)
        failures = sum(1 for b in sim._batches.values() if b.failed)
        avg_wait = float(np.mean([p.days_waiting for p in state.patient_queue])) if state.patient_queue else 0.0
        utilization = 1.0 - (total_idle_intervals / (total_intervals * req.suiteCount)) if total_intervals > 0 else 0.0

        all_infusions.append(infusions)
        all_failures.append(failures)
        all_wait_days.append(avg_wait)
        all_utilization.append(utilization)

    # Weekly throughput = total infusions / (horizon_days / 7)
    weeks = req.timeHorizon / 7.0
    mean_throughput = float(np.mean(all_infusions)) / weeks if weeks > 0 else 0.0

    return {
        "throughput": round(mean_throughput, 1),
        "avgWait": round(float(np.mean(all_wait_days)), 1),
        "utilization": round(float(np.mean(all_utilization)), 2),
        "totalInfusions": round(float(np.mean(all_infusions)), 1),
        "totalFailures": round(float(np.mean(all_failures)), 1),
        "failureRate": round(float(np.mean(all_failures)) / max(float(np.mean(all_infusions)) + float(np.mean(all_failures)), 1) * 100, 1),
    }
