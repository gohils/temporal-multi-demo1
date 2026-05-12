# 📘 Temporal Multi-Domain Worker Architecture (Shared Task Queue Model)

---

# 🧭 1. Architecture Overview

This system implements a **domain-driven workflow execution platform** using Temporal with:

* A **shared task queue**
* Multiple **domain-based workflows**
* Modular **activity execution layer**
* Horizontally scalable **stateless worker runtime**

---

## 🧱 High-Level Architecture

```text
                    ┌──────────────────────────────┐
                    │      Temporal Server         │
                    │  (Workflow state + history)  │
                    └─────────────┬────────────────┘
                                  │
                         Shared Task Queue
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
 ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
 │ Worker Node 1 │       │ Worker Node 2 │       │ Worker Node N │
 │ (stateless)   │       │ (stateless)   │       │ (stateless)   │
 └──────┬────────┘       └──────┬────────┘       └──────┬────────┘
        │                       │                       │
        ├──────────────┬────────┴────────┬──────────────┤
        ▼              ▼                 ▼
  Payments Domain   Invoice Domain    CRM Domain
  Workflows+Acts    Workflows+Acts    Workflows+Acts
```

---

## 🎯 Key Principles

* Workflows are **stateful (Temporal server)**
* Workers are **stateless execution engines**
* Domains are **code-level isolation boundaries**
* Queue is a **routing abstraction, not business logic**

---

# 🧱 2. Domain Structure Pattern

Each business capability is modeled as an **independent domain module**.

---

## 📦 Folder Structure

```text
temporal-worker/
│
├── worker_main.py
│
├── domains/
│   ├── payments/
│   │   ├── workflow.py
│   │   ├── activities.py
│   │
│   ├── invoice/
│   │   ├── workflow.py
│   │   ├── activities.py
│   │
│   ├── crm/
│       ├── workflow.py
│       ├── activities.py
│
└── shared/
    ├── utils.py
    ├── logging.py
    ├── http_client.py
```

---

## 🧠 Domain Rules

Each domain owns:

* Workflows (business orchestration)
* Activities (execution logic)
* Domain-specific validations
* External integrations

---

## 🚫 Anti-patterns

* ❌ shared business logic across domains
* ❌ cross-domain workflow coupling
* ❌ mixing unrelated activities

---

# 👨‍💻 3. Developer Guide — Adding a New Workflow

Example: adding **Fraud Detection domain**

---

## STEP 1 — Create Domain Folder

```text
domains/fraud/
```

---

## STEP 2 — Define Activities

```python
@activity.defn
async def analyze(payload: dict) -> dict:
    return {"score": 0.3}
```

---

## STEP 3 — Define Workflow

```python
@workflow.defn
class FraudWorkflow:

    @workflow.run
    async def run(self, payload):
        result = await workflow.execute_activity(analyze, payload)

        if result["score"] > 0.7:
            return {"status": "BLOCKED"}

        return {"status": "APPROVED"}
```

---

## STEP 4 — Register in Worker

```python
from domains.fraud.workflow import FraudWorkflow
from domains.fraud.activities import analyze
```

Add to worker registry:

```python
WORKFLOWS.append(FraudWorkflow)
ACTIVITIES.append(analyze)
```

---

## STEP 5 — Deploy (No infra changes required)

* Push code
* Restart worker
* New workflows become active

---

# ⚙️ 4. Worker Runtime Model

Workers are **stateless execution engines**.

---

## Worker Responsibilities

* Poll Temporal task queue
* Execute workflow steps
* Execute activities
* Retry failed tasks (via Temporal)
* Report completion

---

## Worker Behavior Model

```text
Workflow Task → Worker → Activity Execution → Result → Temporal Server
```

---

## Key Properties

* Stateless
* Horizontally scalable
* Replaceable at runtime
* No workflow state stored locally

---

# 🔁 5. Failure & Retry Model (Temporal Guarantees)

---

## 🧨 Failure Types

| Failure Type     | Impact                      |
| ---------------- | --------------------------- |
| Activity failure | retried automatically       |
| Worker crash     | execution resumes elsewhere |
| Workflow crash   | state preserved             |
| Network failure  | retry safe                  |

---

## 🔄 Retry Mechanism

Temporal ensures:

* At-least-once execution
* Automatic retries (configurable)
* Deterministic workflow replay

---

## 🧠 Critical Guarantee

> Workflow state is NEVER lost — only execution retries happen

---

## Example Recovery

1. Worker crashes mid-step
2. New worker picks task
3. Workflow resumes from last checkpoint

---

# 🚀 6. Deployment Guide (Docker + Azure)

---

## 🐳 Docker Deployment

### Build image

```bash
docker build -t temporal-worker:latest .
```

---

### Run locally

```bash
docker run -e TASK_QUEUE=shared-task-queue temporal-worker:latest
```

---

## 🐳 Docker Compose (multi-worker)

```yaml
services:
  worker:
    image: temporal-worker:latest
    environment:
      TASK_QUEUE: shared-task-queue
```

---

### Scale workers

```bash
docker compose up --scale worker=5
```

---

## ☁️ Azure Container Apps Deployment

Each worker pool can be deployed as a container app.

---

### Payments Worker

```bash
az containerapp create \
  --name worker-payments \
  --resource-group rg-temporal \
  --environment aca-env \
  --image temporal-worker:latest \
  --env-vars TASK_QUEUE=payments-task-queue
```

---

### Invoice Worker

```bash
az containerapp create \
  --name worker-invoice \
  --resource-group rg-temporal \
  --environment aca-env \
  --image temporal-worker:latest \
  --env-vars TASK_QUEUE=invoice-task-queue
```

---

# 📈 7. Scaling Guide (Replicas + HPA)

---

## 🧠 Scaling Principle

> Scale workers, not workflows

---

## Docker Scaling

```bash
docker compose up --scale worker=5
```

---

## Azure Autoscaling

```bash
az containerapp update \
  --name worker-payments \
  --min-replicas 2 \
  --max-replicas 10
```

---

## Kubernetes HPA (conceptual)

```yaml
metrics:
  - type: CPU
  - type: queue-depth
```

---

## Scaling Model

| Load Type        | Strategy                |
| ---------------- | ----------------------- |
| Low (10–100/day) | 1–2 workers             |
| Medium           | 3–10 workers            |
| High             | queue-based autoscaling |

---

# 🧰 8. Operational Runbook

---

## 🟢 Healthy System

* workers polling normally
* low queue latency
* no retry spikes

---

## 🟡 Degraded System

Symptoms:

* increasing queue backlog
* retry spikes

Actions:

* scale workers
* check activity latency
* inspect external APIs

---

## 🔴 Worker Failure

Symptoms:

* no polling activity
* workflow delays

Actions:

```bash
restart worker deployment
check logs
verify Temporal connectivity
```

---

## 🔴 Activity Failure Spike

Actions:

* inspect external dependency
* check rate limits
* increase retry backoff

---

## 🔁 Deployment Rollback

* redeploy previous container version
* Temporal resumes workflows automatically
* no data loss

---

# 🧠 Final Mental Model

```text
Temporal Server = State Engine
Workers = Stateless Executors
Domains = Code Organization Boundary
Queue = Routing Layer
```

---

# 🎯 Key Takeaway

This architecture is:

✔ Domain-driven
✔ Horizontally scalable
✔ Fault tolerant
✔ Deployment-friendly
✔ Cost-efficient for low–medium workloads

---