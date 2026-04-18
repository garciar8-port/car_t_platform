# CAR-T RL Scheduler — Project Context

> **Purpose of this document:** This is the single source of truth for the CAR-T reinforcement learning scheduler project. It is structured for consumption by AI coding agents (Claude Code) and human engineers. Read this document in full before making any architectural or implementation decisions.

**Project codename:** BioFlow Scheduler (working name)
**Owner:** Rodrigo
**Status:** Pre-MVP / formalization phase
**Last updated:** April 2026

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Problem statement](#2-problem-statement)
3. [Target users & personas](#3-target-users--personas)
4. [Technical architecture](#4-technical-architecture)
5. [MDP formulation](#5-mdp-formulation)
6. [Technology stack](#6-technology-stack)
7. [Repository structure](#7-repository-structure)
8. [Development roadmap](#8-development-roadmap)
9. [Feature catalog](#9-feature-catalog)
10. [Engineering principles](#10-engineering-principles)
11. [Testing & validation strategy](#11-testing--validation-strategy)
12. [Compliance requirements](#12-compliance-requirements)
13. [Glossary](#13-glossary)
14. [Open questions & decisions log](#14-open-questions--decisions-log)

---

## 1. Executive summary

BioFlow Scheduler is an AI-driven optimization layer for autologous cell therapy manufacturing (specifically CAR-T). It sits on top of existing orchestration platforms (Vineti, TrakCel, Binocs) and uses reinforcement learning to produce better scheduling decisions than the rule-based systems currently in use.

**The core insight:** Current cell therapy orchestration platforms handle data tracking and chain-of-identity compliance well, but make scheduling decisions using simple heuristics or manual processes. The combinatorial nature of the problem — variable batch durations, stochastic QC outcomes, time-varying patient acuity, and limited cleanroom capacity — makes this a natural fit for sequential decision-making under uncertainty (i.e., RL).

**Value proposition:** Increase throughput by 10-20% from existing manufacturing capacity without adding cleanrooms or headcount. At CAR-T facility construction costs of $50-300M per site, even a 10% throughput gain represents tens of millions in avoided capex.

**Target customer profile:** Pharma and biotech companies with commercial or late-stage clinical CAR-T operations. Primary targets include AstraZeneca (Rockville MD facility + 8 global sites), Novartis, BMS, Gilead/Kite, and Johnson & Johnson.

---

## 2. Problem statement

### The scheduling problem

Autologous cell therapy manufacturing requires a dedicated batch per patient, where the patient's own T-cells are isolated, genetically modified, expanded, and returned for infusion. This creates a make-to-order manufacturing problem with unusual constraints:

1. **Perishable raw material** — Patient leukapheresis product has a limited viability window.
2. **Stochastic process duration** — Cell expansion varies from 10-21 days depending on patient biology, indication, and transduction efficiency. No two batches are identical.
3. **Capacity bottleneck** — Cleanroom suites are the limiting resource. Each suite handles one batch at a time through a ~14-day process.
4. **QC failure risk** — 10-15% of batches fail release testing, requiring re-manufacture or patient drop-out. Failures are not known until late in the process.
5. **Time-varying patient acuity** — Patients with aggressive disease deteriorate while waiting. A patient's "priority" is a function of how long they've been waiting.
6. **Deterministic serial process** — Once started, a batch cannot be paused, preempted cleanly, or split across suites.
7. **Regulatory constraints** — Every scheduling decision must be auditable (21 CFR Part 11) and defensible to QA and regulatory reviewers.

### Why classical optimization fails

This problem has features that break classical approaches:
- **Integer linear programming** assumes known inputs; batch durations are stochastic.
- **Greedy heuristics** (FIFO, highest-acuity-first) are provably suboptimal and don't handle disruptions well.
- **Static schedules** become invalid the moment a batch fails QC or a new urgent patient arrives.

The problem is a **sequential decision-making problem under uncertainty** — which is precisely what reinforcement learning is designed to solve.

### Why spreadsheets dominate today

Most cell therapy manufacturers still manage scheduling with Excel and whiteboards, supplemented by rule-based tools like Binocs. The reasons are:
- Regulatory comfort — auditable, defensible, well-understood.
- Integration cost — custom optimization tools rarely connect cleanly to existing MES/LIMS/orchestration platforms.
- AI skepticism — pharma operations teams are conservative about black-box recommendations affecting patient care.

BioFlow must address all three concerns to win: compliance-first architecture, pre-built integrations, and full explainability.

---

## 3. Target users & personas

### Primary persona: Manufacturing coordinator

**Role:** Day-to-day scheduler at a cell therapy manufacturing site. Responsible for assigning incoming patient batches to suites, handling disruptions, and coordinating with clinical sites.

**Current pain:**
- Juggles multiple systems (Vineti, MES, LIMS, Excel) to plan each day.
- Re-plans entire schedule manually when a batch fails QC or an urgent patient arrives.
- Gets escalation calls at night when something breaks.
- Blamed when patients wait too long, but has no tools to optimize.

**What they need from BioFlow:**
- A single dashboard showing the current schedule and recommended actions.
- Fast, explainable recommendations they can approve with one click.
- The ability to override the agent when domain expertise says otherwise.
- Alerts when something needs human attention.

### Secondary persona: Manufacturing director

**Role:** Owns the P&L for a cell therapy manufacturing site. Reports to VP of Operations. Cares about throughput, cost per batch, and vein-to-vein time.

**What they need from BioFlow:**
- Executive dashboard with KPIs (utilization, throughput, wait times, failure rates).
- Capacity planning forecasts (30/60/90 day outlook).
- Throughput attribution (how much improvement came from BioFlow vs other factors).
- Board-ready exportable reports.

### Tertiary persona: Data scientist / AI engineer (customer-side)

**Role:** Technical owner of the integration. Validates model performance, monitors for drift, customizes for local conditions.

**What they need from BioFlow:**
- API access to state, actions, and rewards.
- Model version control and A/B comparison tooling.
- Ability to inspect policy decisions (SHAP values, feature importance).
- Continuous learning pipeline with guardrails.

### Quaternary persona: QA / regulatory

**Role:** Ensures the system meets GxP requirements. Signs off on deployment and changes.

**What they need from BioFlow:**
- 21 CFR Part 11 compliant audit trail.
- Model version control with reproducibility.
- Decision explainability for every recommendation.
- Clear separation between validated production models and experimental ones.

---

## 4. Technical architecture

### High-level architecture

The system is organized into six layers, with data flowing downward from external sources to actions, then feeding back upward from the environment/simulator to the state encoder.

```
LAYER 1: DATA SOURCES
├── Vineti / TrakCel (orchestration platforms)
│   └── COI, patient queue, logistics events
├── MES / LIMS (manufacturing execution)
│   └── Batch status, QC data, resource inventory
└── EHR / Clinical systems
    └── Patient acuity scores, clinical updates

         ↓

LAYER 2: STATE CONSTRUCTION
└── State encoder
    └── Transforms raw data into MDP state vector S(t)
        Includes: suite status, patient queue, acuity weights, inventory

         ↓ S(t)

LAYER 3: RL AGENT
├── Policy network π(a|s) — PPO-based
├── Reward shaping module — R = f(wait, idle, fail, infusion)
└── Duration predictor — P(duration | patient, indication)

         ↓ A(t)

LAYER 4: ACTIONS
├── Assign patient → suite (primary action)
├── Delay / expedite batch start
└── Preempt low-acuity batch (emergency only)

         ↓

LAYER 5: ENVIRONMENT (digital twin)
└── Discrete-event simulator
    ├── Cell expansion model (stochastic)
    ├── QC outcome model (Bernoulli)
    └── Patient arrival model (non-homogeneous Poisson)

         ↓ S(t+1), R(t)  [feedback loop back to Layer 2]

LAYER 6: HUMAN-IN-THE-LOOP
└── Manufacturing coordinator
    └── Approve / override / flag recommendations
```

### Component responsibilities

| Layer | Component | Responsibility |
|---|---|---|
| 1 | Data connectors | Pull raw state from external systems. Idempotent, retry-safe. |
| 2 | State encoder | Normalize heterogeneous data into fixed-shape state vector. |
| 3 | Policy network | Map state → action distribution. PPO-based. |
| 3 | Reward shaping | Compute scalar reward from state transition + domain weights. |
| 3 | Duration predictor | Provide expected durations for planning horizon. |
| 4 | Action dispatcher | Translate discrete actions into commands to external systems. |
| 5 | Simulator | Train the policy offline. Also used for what-if analysis in production. |
| 6 | Dashboard | Present recommendations to humans. Collect feedback. |

### Key architectural decisions

**Decision 1: RL sits on top of existing orchestration platforms, does not replace them.**
- Rationale: Vineti and TrakCel handle chain-of-identity and regulatory compliance well. Competing directly triggers long sales cycles. BioFlow adds intelligence without requiring platform migration.
- Implication: All integrations are via API. BioFlow reads from and writes to existing systems.

**Decision 2: Human-in-the-loop is mandatory in MVP.**
- Rationale: Regulatory acceptance of autonomous AI decisions in GxP environments is years away. Coordinators must approve every recommendation.
- Implication: The UI is as important as the model. Optimize for approval speed, not autonomy.

**Decision 3: Offline training on simulator, online inference against real data.**
- Rationale: Cannot train an RL agent on live patient decisions. Must use a digital twin calibrated to historical data.
- Implication: Simulator quality directly determines model quality. Invest in calibration.

**Decision 4: Model versioning and rollback are P1 features.**
- Rationale: QA will not approve a system they cannot audit or revert.
- Implication: Every deployed policy is a tagged artifact with reproducible training data.

**Decision 5: Explainability is architectural, not bolted on.**
- Rationale: Coordinators will not trust black-box recommendations. QA will not approve them.
- Implication: SHAP values or equivalent are computed alongside every recommendation, not as a separate batch job.

---

## 5. MDP formulation

The scheduling problem is formalized as a Markov Decision Process:

### State space S

The state at time *t* is a vector combining:

```python
State = {
    'suites': [
        {
            'id': str,
            'status': Enum['idle', 'in_use', 'cleaning', 'maintenance'],
            'current_batch_id': Optional[str],
            'current_phase': Enum['isolation', 'activation', 'transduction',
                                  'expansion', 'harvest', 'formulation', 'qc'],
            'days_remaining_estimate': float,
            'days_remaining_variance': float
        }
        for suite in facility.suites
    ],
    'patient_queue': [
        {
            'patient_id': str,
            'indication': str,
            'acuity_score': float,  # 0-1, higher = more urgent
            'days_waiting': int,
            'cell_viability_days_remaining': int,
            'scheduled_leukapheresis_date': Optional[date],
            'cells_collected_date': Optional[date]
        }
        for patient in patient_queue
    ],
    'inventory': {
        'media_units': int,
        'viral_vector_doses': int,
        'reagent_kits': int,
    },
    'incoming_pipeline': [
        {
            'patient_id': str,
            'estimated_arrival_days': int,
            'priority': float
        }
        for patient in scheduled_intake
    ],
    'clock': datetime
}
```

### Action space A

Actions are discrete and scoped to minimize the combinatorial explosion. In MVP, the action space is:

```python
Action = {
    'type': 'assign',
    'patient_id': str,
    'suite_id': str,
    'start_time': datetime
}
# Or
Action = {
    'type': 'no_op'  # Wait for next decision point
}
```

In P2, the action space expands to include:

```python
Action = {
    'type': 'delay',
    'batch_id': str,
    'new_start_time': datetime
}
Action = {
    'type': 'expedite',
    'batch_id': str
}
Action = {
    'type': 'preempt',
    'current_batch_id': str,
    'incoming_patient_id': str,
    'justification': str
}
```

### Transition dynamics P(s' | s, a)

Transitions are stochastic and driven by the simulator. Key stochastic elements:

- **Cell expansion duration:** Drawn from `LogNormal(μ, σ)` calibrated per indication. Parameters: `μ = log(14 days)`, `σ = 0.15` as baseline.
- **QC outcome:** Bernoulli with `p = 0.88` baseline, varying by batch history.
- **Patient arrivals:** Non-homogeneous Poisson process with rate `λ(t)` varying by day of week and season.
- **Equipment downtime:** Exponentially distributed failure intervals, uniform repair times.

### Reward function R(s, a, s')

The reward function is a linear combination of operational objectives:

```
R = -α * wait_time_increase
    - β * suite_idle_time
    - γ * batch_failure_penalty
    + δ * successful_infusion_reward
    - ε * constraint_violation_penalty
```

Default weights (to be tuned with customer data):
- `α = 1.0` (per patient-day of wait)
- `β = 0.2` (per suite-day idle)
- `γ = 50.0` (per batch failure)
- `δ = 100.0` (per successful infusion)
- `ε = 1000.0` (per hard constraint violation)

The weights must be calibrated through interviews with manufacturing coordinators. This is where domain expertise is irreplaceable.

### Discount factor γ

`γ = 0.95` for the RL discount factor (different from the batch failure penalty weight γ above — rename one of these in code to avoid confusion).

---

## 6. Technology stack

### Runtime stack

| Layer | Technology | Rationale |
|---|---|---|
| Simulation | SimPy + OpenAI Gymnasium | Standard discrete-event simulation + RL interface |
| RL framework | Stable Baselines3 (PPO) | Production-ready, well-documented, stable training |
| Duration prediction | scikit-learn / PyTorch | Start simple (gradient boosting), upgrade to neural net if needed |
| API layer | FastAPI + Pydantic | Modern Python, strong type safety, auto OpenAPI docs |
| Data layer | PostgreSQL + SQLAlchemy | Standard relational DB, ACID guarantees for audit trail |
| Caching / queue | Redis | Session state, job queue, real-time updates |
| Frontend | React 18 + TypeScript + Recharts | Standard modern frontend, type safety |
| Infrastructure | AWS (ECS, RDS, S3) + Docker | Enterprise-standard, HIPAA/GxP compliant options |
| Monitoring | OpenTelemetry + Grafana | Vendor-neutral observability |
| CI/CD | GitHub Actions | Standard |
| Model registry | MLflow | Experiment tracking, model versioning, reproducibility |

### Development stack

- Python 3.11+ (backend, ML)
- Node 20+ (frontend)
- Poetry (Python dependency management)
- pnpm (JavaScript dependency management)
- Ruff + Black (Python linting/formatting)
- ESLint + Prettier (JavaScript linting/formatting)
- pytest (Python testing)
- Vitest + Playwright (JavaScript unit + E2E testing)

### Why these choices

- **SimPy over custom simulator:** Battle-tested DES library. Avoid reinventing the wheel.
- **Stable Baselines3 over custom RL:** Production-grade implementations of PPO, DQN, SAC. Do not build RL algorithms from scratch.
- **FastAPI over Flask/Django:** Type safety, async support, auto-documentation, modern Python idioms.
- **PostgreSQL over NoSQL:** Audit trail requires ACID guarantees and relational integrity. Regulatory environments prefer well-understood databases.
- **React over Vue/Svelte:** Largest talent pool, widest library ecosystem, lowest risk in enterprise sales context.
- **AWS over GCP/Azure:** Largest pharma customer footprint, most mature HIPAA/GxP tooling.

### What NOT to use

- **Do not use LangChain** for this project. No LLM orchestration is required in the core scheduler. LLMs may be used for explainability (generating natural-language summaries of decisions) but as a separate module.
- **Do not use MongoDB** or other NoSQL stores for primary data. Audit trail needs ACID.
- **Do not use client-side state managers** beyond React Query for server state. Keep the frontend simple.
- **Do not use localStorage / sessionStorage** for anything that needs to persist across sessions — use the backend.

---

## 7. Repository structure

The recommended monorepo structure:

```
bioflow-scheduler/
├── README.md
├── PROJECT_CONTEXT.md          # this document
├── pyproject.toml               # Python workspace
├── package.json                 # JS workspace
├── docker-compose.yml           # local dev
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── build.yml
│       └── deploy.yml
├── services/
│   ├── api/                     # FastAPI backend
│   │   ├── src/bioflow_api/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   ├── models/          # Pydantic schemas
│   │   │   ├── db/              # SQLAlchemy models
│   │   │   ├── integrations/    # Vineti, TrakCel, MES adapters
│   │   │   └── services/        # business logic
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── scheduler/               # RL agent + inference
│   │   ├── src/bioflow_scheduler/
│   │   │   ├── mdp/             # state, action, reward definitions
│   │   │   ├── policy/          # PPO policy wrapper
│   │   │   ├── simulator/       # SimPy environment
│   │   │   ├── duration_model/  # duration predictor
│   │   │   └── explainer/       # SHAP integration
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── frontend/                # React dashboard
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   ├── hooks/
│       │   ├── api/             # typed API client
│       │   └── types/
│       ├── tests/
│       └── package.json
├── packages/
│   └── shared-types/            # TypeScript types generated from Pydantic
├── training/
│   ├── configs/                 # hyperparameter configs
│   ├── scripts/                 # training entry points
│   ├── experiments/             # MLflow tracking dir
│   └── data/                    # synthetic + historical data
├── docs/
│   ├── architecture/
│   ├── api/                     # auto-generated OpenAPI
│   └── runbooks/                # operational guides
└── scripts/
    ├── setup-dev.sh
    ├── seed-db.sh
    └── generate-synthetic-data.py
```

### Module boundaries

**Critical principle:** The `scheduler` service must be usable independently of the `api` service. This allows training, evaluation, and what-if analysis without running the full stack. The API is a thin wrapper around the scheduler's Python interface.

**Dependency direction:**
- `api` depends on `scheduler` (for inference) and `shared-types`.
- `scheduler` depends on nothing in this repo. It's a standalone Python library.
- `frontend` depends on `shared-types` only (for TypeScript types generated from API schemas).

---

## 8. Development roadmap

Development is organized into five phases. Each phase produces independently valuable output.

### Phase 1: Problem formalization & data mapping (Weeks 1-3)

**Goal:** Get the MDP right on paper before writing code.

**Tasks:**
1. Write MDP specification document (formal S, A, P, R, γ definitions).
2. Map each state variable to a real data source (Vineti field, MES field, etc.).
3. Design reward function draft with customer-interview-derived weights.
4. Collect or synthesize training data distributions from published literature.
5. Create initial Pydantic schemas for state and action objects.

**Deliverable:** `docs/architecture/mdp-specification.md` + `services/scheduler/src/bioflow_scheduler/mdp/schemas.py`

**Acceptance criteria:**
- A new engineer reading the MDP spec can explain the state, action, and reward without asking questions.
- Every field in the state schema has a documented data source.
- The reward function has explicit weights with justifications.

### Phase 2: Build the discrete-event simulator (Weeks 3-6)

**Goal:** A working digital twin of a cell therapy manufacturing facility.

**Tasks:**
1. Implement SimPy environment with suites as resources.
2. Model the 7-step batch process (isolation → QC) with configurable durations.
3. Add stochastic duration, QC outcomes, and patient arrivals.
4. Wrap in OpenAI Gymnasium interface (`reset`, `step`, `render`).
5. Implement baseline heuristics (FIFO, highest-acuity-first, shortest-processing-time-first).
6. Benchmark baselines on synthetic data to establish target metrics.

**Deliverable:** `services/scheduler/src/bioflow_scheduler/simulator/` + baseline benchmark results.

**Acceptance criteria:**
- Simulator runs 1000 patient trajectories in under 30 seconds on a laptop.
- All three baseline heuristics produce repeatable results with fixed seeds.
- Baseline metrics (throughput, avg wait time) match published CAR-T operational data within reasonable bounds.

### Phase 3: Train the RL agent (Weeks 6-10)

**Goal:** A PPO policy that provably beats all baselines in simulation.

**Tasks:**
1. Start with tabular Q-learning on a toy problem (2 suites, 5 patients) for sanity check.
2. Implement DQN with continuous state features as an intermediate step.
3. Implement PPO using Stable Baselines3. Do NOT build from scratch.
4. Set up hyperparameter tuning with Optuna (learning rate, discount factor, reward weights).
5. Track experiments with MLflow.
6. Run evaluation against all baselines with statistical significance testing.

**Deliverable:** Trained PPO policy with evaluation report showing statistically significant improvement over baselines.

**Acceptance criteria:**
- PPO policy beats all three baselines on both throughput and avg wait time (p < 0.05).
- Training is reproducible from config file + seed.
- Policy is loadable from a single artifact for inference.

### Phase 4: Expand complexity & validate (Weeks 10-14)

**Goal:** Production-ready model with full action space and explainability.

**Tasks:**
1. Expand action space to include delay/expedite and emergency preemption.
2. Add resource inventory to state (media, viral vectors).
3. Stress test with adversarial scenarios (QC failure waves, equipment downtime, patient surges).
4. Validate against historical scheduling decisions from a pilot customer.
5. Implement SHAP-based explainability layer.
6. Add drift detection to duration prediction model.

**Deliverable:** Validation report + explainability API.

**Acceptance criteria:**
- Agent handles adversarial scenarios without catastrophic failures.
- Historical replay shows agent would have improved on real decisions by X%.
- SHAP values are computed in < 100ms per decision.

### Phase 5: Productionize & integrate (Weeks 14-20)

**Goal:** Deployable product with API, dashboard, compliance layer, and integrations.

**Tasks:**
1. Build FastAPI service wrapping the trained policy.
2. Implement Vineti and TrakCel adapters (or mock versions if API access is unavailable).
3. Build React dashboard with Gantt view, patient queue, and approval workflow.
4. Implement 21 CFR Part 11 audit trail with cryptographic signatures.
5. Add RBAC with SSO integration (SAML/OIDC).
6. Deploy to staging AWS environment with full observability.

**Deliverable:** Deployable MVP product that a customer could pilot.

**Acceptance criteria:**
- End-to-end demo: new patient arrives → agent recommends → coordinator approves → schedule updates.
- Audit trail captures every state change with user attribution.
- Staging environment passes a security review.

---

## 9. Feature catalog

Features are organized into three priority tiers. **Tier 1 (P1) is MVP**, required for any deployable version. **Tier 2 (P2) is fast-follow**, expected within 6 months of MVP. **Tier 3 (P3) is differentiators**, the long-term moat.

### Tier 1: MVP features (P1)

#### Core scheduling engine

| Feature | Description | Primary user |
|---|---|---|
| Patient-to-suite assignment | PPO policy assigns incoming patient batches to available suites | Ops coordinator |
| Stochastic duration modeling | Log-normal distributions with confidence intervals per indication | Mfg director |
| Rolling-horizon re-optimization | Schedule recomputes on state change (new patient, QC failure, downtime) | Ops coordinator |
| Baseline heuristic fallback | FIFO fallback if agent confidence drops below threshold | System |

#### Coordinator dashboard

| Feature | Description | Primary user |
|---|---|---|
| Gantt schedule view | Visual timeline per suite with drag-to-override | Ops coordinator |
| Patient queue triage panel | Ranked list with acuity, days waiting, recommended action | Ops coordinator |
| Approve / override / flag workflow | One-click approval with required justification on override | Ops coordinator |
| Real-time KPI tiles | Utilization, wait time, throughput, failure rate | Mfg director |

#### Data integration

| Feature | Description | Primary user |
|---|---|---|
| Vineti / TrakCel connector | Bidirectional REST API sync for COI and patient status | IT / integrations |
| MES / LIMS adapter | Reads batch progress, QC results, resource inventory | IT / integrations |
| CSV / spreadsheet import | Fallback bulk upload for sites without modern MES | Ops coordinator |
| State snapshot API | Read-only endpoint for BI tools and reporting | Analytics team |

#### Compliance & audit

| Feature | Description | Primary user |
|---|---|---|
| 21 CFR Part 11 audit trail | Every action logged with user, timestamp, crypto signature | QA / regulatory |
| Role-based access control | Granular permissions with SSO (SAML/OIDC) | IT security |
| Model version control | Versioned, signed, reproducible policies with rollback | QA / regulatory |
| Decision explainability panel | Top 3 SHAP factors for every recommendation | QA / regulatory |

### Tier 2: Fast-follow features (P2)

#### Advanced scheduling

- Emergency preemption with impact analysis
- Expedite / delay recommendations for resource smoothing
- Resource inventory joint optimization
- Automated QC re-scheduling cascade

#### Simulation & what-if

- Scenario sandbox for capacity planning
- 30/60/90 day capacity forecasts
- Stress test mode with synthetic disruptions
- Policy A/B comparison on historical data

#### Analytics & reporting

- Vein-to-vein time dashboard sliced by cohort
- Throughput attribution (ROI proof)
- Bottleneck heatmap
- Exportable board-level reports

#### Collaboration

- Shift handoff notes
- Slack / Teams alerting
- Cross-functional batch comments

### Tier 3: Differentiators (P3)

#### Multi-site orchestration

- Cross-site patient routing
- Global load balancing across regions
- Cold chain logistics integration
- Time-zone aware scheduling

#### Continuous learning

- Online policy fine-tuning from overrides
- Duration model auto-calibration with drift detection
- Federated learning across customer sites
- Anomaly detection

#### Patient-facing features

- Patient portal integration with treatment timeline
- Clinician coordination view
- Bridging therapy coordination

#### Platform extensibility

- Custom reward function builder UI
- Plugin architecture for new cell therapy products
- Anonymized cross-customer benchmarking
- Public API marketplace

---

## 10. Engineering principles

### Code quality

1. **Type everything.** Python: use type hints everywhere, enforce with mypy. TypeScript: no `any` in production code.
2. **Test the hard parts.** Unit tests for MDP transitions, reward calculation, and state encoding are non-negotiable. UI tests can be lighter.
3. **Seed randomness.** Every stochastic operation accepts a seed. Reproducibility is a compliance requirement.
4. **Log everything important.** Use structured logging (JSON). Include user ID, request ID, and model version on every relevant log line.
5. **Fail loud in dev, fail gracefully in prod.** Development mode raises exceptions on invariant violations. Production logs and falls back to baseline heuristics.

### API design

1. **Versioned from day one.** All endpoints under `/api/v1/`. Breaking changes go to `/api/v2/`.
2. **Idempotent writes.** Every mutating endpoint accepts an `Idempotency-Key` header.
3. **Pagination everywhere.** No unbounded list endpoints. Default page size 50, max 200.
4. **Typed errors.** Use a discriminated union of error types, not strings.

### State management

1. **Source of truth is PostgreSQL.** The frontend and the scheduler both read from the DB. No cross-service state.
2. **Optimistic UI for approvals.** Approving a recommendation shows immediate feedback, reconciles with server.
3. **Immutable audit records.** Audit trail entries are append-only. Corrections are new entries, not edits.

### Security

1. **No secrets in code.** Use AWS Secrets Manager. Pre-commit hook blocks hardcoded secrets.
2. **Encrypt at rest and in transit.** PostgreSQL encrypted volumes, TLS 1.3 on all connections.
3. **Audit all auth events.** Login, logout, permission changes, and token refreshes are logged.
4. **Principle of least privilege.** Services assume IAM roles with minimal permissions. No long-lived credentials.

### ML engineering

1. **Models are artifacts, not code.** Every deployed policy is a file in S3 with a version tag and metadata.
2. **Training is reproducible.** Given the same config file and seed, training produces the same model.
3. **Evaluation is automatic.** Every new model is automatically evaluated against baselines before promotion.
4. **Monitor for drift.** Input distributions and prediction distributions are tracked. Alert on significant drift.

---

## 11. Testing & validation strategy

### Unit tests

- MDP state encoder: test edge cases (empty queue, full facility, missing data).
- Reward function: verify correctness of each component.
- Simulator: test that deterministic seeds produce identical trajectories.
- Baseline heuristics: verify they produce expected behavior on simple inputs.
- API endpoints: test happy path + common error paths.

### Integration tests

- End-to-end simulation run: from reset to terminal state.
- API → Scheduler → DB round trip: verify state consistency.
- Frontend → API → Scheduler: verify UI actions produce correct backend changes.

### Validation tests

- **Historical replay:** Feed real historical decisions into the simulator. Compare agent's proposed schedule to what actually happened. Measure delta in wait time and utilization.
- **Stress scenarios:** Run agent through adversarial scenarios (QC failure waves, patient surges). Verify graceful degradation.
- **Baseline comparison:** Verify trained policy beats all three baselines with statistical significance (p < 0.05, minimum 100 episode runs).

### Validation metrics

Primary metrics (must improve vs baseline):
- Average patient wait time (days from apheresis to infusion)
- Suite utilization (percentage of productive time)
- Throughput (successful infusions per week)

Secondary metrics (must not regress):
- Batch failure rate (should remain stable)
- Constraint violations (should be zero)
- Decision latency (should be < 1 second)

---

## 12. Compliance requirements

### 21 CFR Part 11 requirements

The system must comply with FDA 21 CFR Part 11 for electronic records and signatures:

1. **Audit trail:** Every create, read, update, delete operation must be logged with timestamp, user, and action.
2. **Electronic signatures:** Critical actions (approve, override, deploy new model) require authenticated e-signature.
3. **System validation:** The system itself must be validated per computerized system validation (CSV) guidelines.
4. **Access controls:** Unique user accounts, no shared credentials, automatic lockout on inactivity.
5. **Data integrity:** ALCOA+ principles (Attributable, Legible, Contemporaneous, Original, Accurate, plus Complete, Consistent, Enduring, Available).

### GxP implications

- **GMP (Good Manufacturing Practice):** The scheduler impacts manufacturing decisions, so it is in scope.
- **GDP (Good Documentation Practice):** All documentation must follow GDP conventions.
- **GAMP 5 (Good Automated Manufacturing Practice):** The system will likely be classified as Category 4 (configured software) or Category 5 (custom software).

### Design implications

- All model decisions must be reproducible and explainable.
- Model training data must be versioned and traceable.
- Changes to the reward function or policy require QA approval workflow.
- Production models are immutable; updates require new version + validation.

### What is OUT of scope for MVP

- Full CSV / system validation (comes before first production deployment, not before MVP).
- Integration with clinical EDC systems.
- PHI handling beyond patient IDs and acuity scores (no full clinical records).

---

## 13. Glossary

| Term | Definition |
|---|---|
| **Autologous** | Cell therapy derived from the patient's own cells (vs allogeneic, which uses donor cells). |
| **CAR-T** | Chimeric Antigen Receptor T-cell therapy. T-cells engineered to target cancer. |
| **CDMO** | Contract Development and Manufacturing Organization. |
| **Cleanroom suite** | Isolated, controlled-environment manufacturing space for a single batch. |
| **COI** | Chain of Identity. Tracks which cells belong to which patient throughout manufacturing. |
| **COC** | Chain of Custody. Tracks physical handling and logistics. |
| **GxP** | Good "X" Practice, where X = Manufacturing, Documentation, Clinical, Laboratory, etc. |
| **Leukapheresis** | Process of collecting white blood cells from a patient's blood. |
| **Lentiviral transduction** | Using a virus to insert genetic material (the CAR gene) into T-cells. |
| **MES** | Manufacturing Execution System. Software that tracks manufacturing operations. |
| **LIMS** | Laboratory Information Management System. Software for lab sample tracking. |
| **MDP** | Markov Decision Process. Formal framework for sequential decision-making. |
| **PPO** | Proximal Policy Optimization. A policy-gradient RL algorithm. |
| **QC release** | Quality control testing that determines if a batch can be infused. |
| **RL** | Reinforcement Learning. |
| **Vein-to-vein time** | Total time from patient's blood collection to infusion of the final product. |

---

## 14. Open questions & decisions log

This section is a running log of decisions that need input or have been made. Add new entries at the top.

### Open questions

- **Pricing model:** SaaS subscription vs per-batch fee vs hybrid? Depends on customer discovery.
- **Initial target customer:** AstraZeneca (aggressive scaling, 8 sites) vs Kite (known network from prior experience) vs CDMO (broader market)?
- **Synthetic vs real training data:** Can we source historical manufacturing data from any partner, or must MVP be trained on fully synthetic data?
- **Multi-tenancy from day one:** Should the architecture support multiple customers in a single instance, or deploy single-tenant?

### Decisions made

| Date | Decision | Rationale |
|---|---|---|
| 2026-04 | Use PPO as primary RL algorithm | Well-established, stable, good fit for continuous state spaces with discrete actions |
| 2026-04 | Build on top of Vineti/TrakCel, not replace | Avoids competing with incumbents; focuses on intelligence layer |
| 2026-04 | Human-in-the-loop mandatory for MVP | Regulatory acceptance; trust-building |
| 2026-04 | Simulator-first training approach | Cannot train on real patient decisions; need digital twin |
| 2026-04 | FastAPI + React + PostgreSQL stack | Enterprise-standard, low-risk, maximum talent pool |
| 2026-04 | AWS as primary cloud | Largest pharma customer footprint; best GxP tooling |
| 2026-04 | MLflow for model registry | Open-source, vendor-neutral, well-integrated with Python ML ecosystem |

---

## Appendix A: Quick start for Claude Code

When working on this project, Claude Code should:

1. **Read this document in full before making architectural decisions.**
2. **Check the glossary for any domain term before assuming its meaning.**
3. **Default to the tech stack in section 6. Do not introduce new dependencies without justification.**
4. **Follow the repository structure in section 7. Do not flatten or reorganize without discussion.**
5. **Respect module boundaries:** `scheduler` must be independently usable; `frontend` only depends on `shared-types`.
6. **When implementing a feature, check the priority tier in section 9.** P1 features can be built directly; P2/P3 features require explicit confirmation.
7. **Write tests proportional to the risk.** MDP logic and reward functions need extensive unit tests; UI components need lighter coverage.
8. **Every stochastic operation must accept a seed parameter.**
9. **Never hardcode domain parameters** (reward weights, duration distributions, QC failure rates). Use config files.
10. **Ask clarifying questions before making irreversible decisions** (database schema changes, API contract changes, model architecture changes).

## Appendix B: Phase 1 starter task list

For an agent beginning work on this project, the immediate Phase 1 tasks are:

1. Create the monorepo structure per section 7.
2. Implement Pydantic schemas for `State`, `Action`, `Reward` in `services/scheduler/src/bioflow_scheduler/mdp/schemas.py`.
3. Write the MDP specification document in `docs/architecture/mdp-specification.md`.
4. Create a minimal SimPy environment with 2 suites, deterministic durations, and FIFO baseline.
5. Wrap the SimPy environment in a Gymnasium interface.
6. Write unit tests for state transitions and reward calculation.
7. Set up CI pipeline with type checking, linting, and tests.

Each of these tasks is independently completable and does not require the later phases to be planned in detail.

---

**End of PROJECT_CONTEXT.md**
