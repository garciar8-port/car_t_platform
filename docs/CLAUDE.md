# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BioFlow Scheduler — an AI-driven optimization layer for autologous CAR-T cell therapy manufacturing. Uses reinforcement learning (PPO) to schedule patient batches across cleanroom suites, sitting on top of existing orchestration platforms (Vineti, TrakCel). Currently in pre-MVP / formalization phase.

Read `PROJECT_CONTEXT.md` in full before making architectural or implementation decisions. It is the single source of truth.

## Tech Stack

| Layer | Technology |
|---|---|
| Simulation | SimPy + OpenAI Gymnasium |
| RL | Stable Baselines3 (PPO) |
| Duration prediction | scikit-learn (start simple) |
| API | FastAPI + Pydantic |
| Database | PostgreSQL + SQLAlchemy |
| Cache/queue | Redis |
| Frontend | React 18 + TypeScript + Recharts |
| Infra | AWS (ECS, RDS, S3) + Docker |
| Monitoring | OpenTelemetry + Grafana |
| Model registry | MLflow |

**Dev tooling:** Python 3.11+ (Poetry), Node 20+ (pnpm), Ruff + Black, ESLint + Prettier, pytest, Vitest + Playwright.

**Do NOT use:** LangChain, MongoDB/NoSQL for primary data, client-side state managers beyond React Query, localStorage for persistent data.

## Build & Dev Commands

*Not yet established — project is pre-MVP with no code. Once the monorepo is scaffolded:*

```bash
# Python (services/scheduler, services/api)
poetry install
poetry run pytest
poetry run ruff check .
poetry run mypy .

# Frontend (services/frontend)
pnpm install
pnpm dev
pnpm test
pnpm lint

# Full stack
docker-compose up
```

## Architecture

### Monorepo Structure (planned)

```
services/
├── api/              # FastAPI backend — thin wrapper around scheduler
├── scheduler/        # RL agent, simulator, MDP — standalone Python library
└── frontend/         # React dashboard
packages/
└── shared-types/     # TypeScript types generated from Pydantic schemas
training/             # Configs, scripts, experiments, data
```

### Module Boundaries (critical)

- `scheduler` must be independently usable (no dependency on `api` or `frontend`)
- `api` depends on `scheduler` and `shared-types`
- `frontend` depends only on `shared-types`

### Six-Layer Data Flow

1. **Data sources** → Vineti/TrakCel, MES/LIMS, EHR
2. **State encoder** → Transforms raw data into MDP state vector
3. **RL agent** → PPO policy π(a|s), reward shaping, duration predictor
4. **Actions** → Assign patient→suite, delay/expedite, preempt
5. **Simulator** → SimPy discrete-event digital twin (stochastic durations, QC outcomes, patient arrivals)
6. **Human-in-the-loop** → Coordinator approves/overrides recommendations

## Key Design Constraints

- **Human-in-the-loop is mandatory** — coordinators must approve every recommendation
- **Every stochastic operation must accept a seed parameter** — reproducibility is a compliance requirement
- **Never hardcode domain parameters** (reward weights, duration distributions, QC failure rates) — use config files
- **21 CFR Part 11 compliance** — immutable audit trail, e-signatures, model version control
- **Explainability is architectural** — SHAP values computed alongside every recommendation, not as a separate job
- **All API endpoints versioned** under `/api/v1/`, idempotent writes, paginated lists (default 50, max 200)

## MDP Quick Reference

- **State:** Suite statuses, patient queue (with acuity scores), inventory, incoming pipeline, clock
- **Actions (MVP):** Assign patient→suite or no-op
- **Reward:** Linear combination — penalize wait time, idle time, failures; reward successful infusions; heavily penalize constraint violations
- **Transitions:** Stochastic — LogNormal expansion durations, Bernoulli QC (p=0.88), Poisson arrivals
- **Discount:** γ = 0.95

## Development Phases

1. **Problem formalization & data mapping** — MDP spec, Pydantic schemas
2. **Discrete-event simulator** — SimPy + Gymnasium wrapper + baseline heuristics (FIFO, highest-acuity, shortest-processing)
3. **Train RL agent** — Tabular Q-learning → DQN → PPO via Stable Baselines3, Optuna tuning, MLflow tracking
4. **Expand complexity** — Full action space, resource inventory, SHAP explainability, adversarial stress testing
5. **Productionize** — FastAPI service, React dashboard, Vineti/TrakCel adapters, audit trail, RBAC, AWS deployment

## Glossary (key terms)

- **Autologous** — therapy from patient's own cells
- **CAR-T** — Chimeric Antigen Receptor T-cell therapy
- **COI** — Chain of Identity (tracks which cells belong to which patient)
- **Vein-to-vein time** — total time from blood collection to infusion
- **Leukapheresis** — collecting white blood cells from patient
- **QC release** — quality control testing determining if a batch can be infused
