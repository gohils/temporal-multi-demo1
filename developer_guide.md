# 📘 Temporal Multi-Domain Shared Worker Pattern

## 🧭 Overview

This architecture implements:

* One **shared Temporal Task Queue**
* Multiple **domain-based workflows**
* Multiple **domain-based activities**
* One or more **shared worker runtimes**
* Strong **code-level domain isolation (not infra explosion)**

---

## 🧱 Core Idea

Instead of:

> ❌ 1 worker per workflow (overkill microservices)

or

> ❌ 1 giant monolithic worker file (unstructured)

We use:

> ✔ One worker runtime + modular domain plugins

---

# 🏗 Architecture Diagram (Mental Model)

```
                    ┌──────────────────────────┐
                    │   Temporal Server        │
                    │ (source of truth/state)  │
                    └──────────┬───────────────┘
                               │
                 shared-task-queue (routing layer)
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                             │
┌───────▼────────┐                          ┌─────────▼────────┐
│ Worker Runtime │                          │ Worker Runtime  │
│ (replica 1)    │                          │ (replica 2)     │
└───────┬────────┘                          └─────────┬────────┘
        │                                             │
        └──────────────┬──────────────┬──────────────┘
                       │              │
          ┌────────────▼───┐  ┌──────▼────────┐  ┌────────────▼──────┐
          │ Payments Domain│  │ Invoice Domain│  │ CRM Domain        │
          │ workflows+acts  │  │ workflows+acts│  │ workflows+acts    │
          └─────────────────┘  └───────────────┘  └───────────────────┘
```

---

# 📦 Project Structure

```
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
    ├── logging.py
    ├── utils.py
    ├── http_client.py
```

---

# ⚙️ Core Design Principles

## 1. Domain Isolation (Code Level)

Each domain owns:

* workflows
* activities
* business logic
* dependencies

---

## 2. Shared Execution Layer (Worker)

One worker:

* loads all domains
* executes all workflows
* polls one task queue

---

## 3. Temporal Guarantees

* workflow state is persisted in server
* worker is stateless execution engine
* failures do NOT lose workflow state

---

# 🚀 Step-by-Step Developer Guide

---

# STEP 1 — Create a New Domain

Example: adding a new use case → **“Fraud Detection”**

```
domains/fraud/
```

---

# STEP 2 — Define Activities

📄 `domains/fraud/activities.py`

```python
from temporalio import activity
import asyncio


@activity.defn
async def analyze_transaction(payload: dict) -> dict:
    print("[FRAUD] analyzing transaction")

    await asyncio.sleep(1)

    score = 0.2  # dummy logic

    return {"fraud_score": score}


@activity.defn
async def block_transaction(payload: dict) -> dict:
    print("[FRAUD] blocking transaction")

    await asyncio.sleep(1)

    return {"blocked": True}
```

---

# STEP 3 — Define Workflow

📄 `domains/fraud/workflow.py`

```python
from temporalio import workflow
from datetime import timedelta
from .activities import analyze_transaction, block_transaction


@workflow.defn
class FraudWorkflow:

    @workflow.run
    async def run(self, payload: dict):

        result = await workflow.execute_activity(
            analyze_transaction,
            payload,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if result["fraud_score"] > 0.7:
            await workflow.execute_activity(
                block_transaction,
                payload,
                start_to_close_timeout=timedelta(seconds=10),
            )

            return {"status": "BLOCKED"}

        return {"status": "APPROVED"}
```

---

# STEP 4 — Register Domain in Worker

Update `worker_main.py`

```python
from domains.fraud.workflow import FraudWorkflow
from domains.fraud.activities import *
```

Then add:

```python
WORKFLOWS = [
    PaymentWorkflow,
    InvoiceWorkflow,
    CRMWorkflow,
    FraudWorkflow,   # NEW
]

ACTIVITIES = [
    validate_payment,
    charge_payment,

    generate_invoice,
    send_invoice,

    update_customer,
    sync_salesforce,

    analyze_transaction,
    block_transaction,
]
```

---

# STEP 5 — Deploy Worker (no change needed)

```bash
docker build -t temporal-worker .
docker run temporal-worker
```

OR:

```bash
python worker_main.py
```

---

# STEP 6 — Run Workflow

Example client call:

```python
await client.start_workflow(
    FraudWorkflow.run,
    {
        "transaction_id": "TX123",
        "amount": 5000
    },
    id="fraud-1",
    task_queue="shared-task-queue",
)
```

---

# 🧠 Operational Behavior

## ✔ If CRM domain breaks:

* CRM workflows fail
* Payments + Invoice unaffected

---

## ✔ If worker crashes:

* workflows pause safely
* state preserved in Temporal
* restart resumes automatically

---

## ✔ If fraud domain added:

* no infra change
* only worker registry update

---

# ⚖️ Failure Isolation Model

| Failure Type     | Impact Scope                  |
| ---------------- | ----------------------------- |
| workflow bug     | single workflow type          |
| activity failure | single step retry             |
| worker crash     | temporary pause (all domains) |
| dependency bug   | shared if reused              |

---

# 🔁 Scaling Model

## Low frequency (your case: 10–100/day)

* 1 worker pool
* shared queue
* domain modules

---

## Medium scale

* 2–3 worker pools
* split by SLA or domain group

---

## High scale

* separate queues per domain
* autoscaled worker groups

---

# 🏢 Team Structure Mapping

| Domain   | Ownership      |
| -------- | -------------- |
| payments | Payments team  |
| invoice  | Finance team   |
| CRM      | Sales ops team |
| fraud    | Risk team      |

Each team:

* owns folder
* owns workflows
* owns activities
* does NOT own infrastructure

---

# 🧩 Key Design Insight

This pattern is:

> ✔ Domain-Driven Design (DDD) at code level
> ✔ Shared execution engine at runtime level
> ✔ Temporal-managed state at system level

NOT:

> ❌ monolith
> ❌ microservice explosion
> ❌ per-workflow containers

---

# 🚨 When NOT to use this pattern

Avoid shared worker model when:

* strict regulatory isolation is required (finance vs healthcare)
* extreme SLA differences exist (ms vs hours)
* very high throughput per domain
* different security boundaries per domain

---

# 🧭 Final Summary

This architecture gives you:

### ✔ Benefits

* low infra cost
* simple deployment
* strong domain separation in code
* Temporal-native reliability
* easy onboarding of new workflows

### ✔ Trade-off

* shared runtime (mitigated by replicas)
* requires discipline in dependency management

---
Yes — you **should absolutely add parts of this**, but not all of it in raw form.

What you pasted is already close to a **production-grade deployment guide**, but it needs to be **cleanly integrated into your Temporal “developer pattern document”** so it doesn’t become “infra noise mixed with architecture”.

Let’s structure it properly.

---

# 📘 Where this fits in your Temporal Guide

Your guide should have **4 layers**:

## 1. Architecture Pattern (you already have this)

* shared task queue
* domain modules
* worker runtime model

## 2. Developer Guide (how to add new workflow)

* create domain
* add activities
* register workflow
* update worker_main

## 3. Runtime Execution Model

* Temporal guarantees
* retries
* failure isolation

## 4. 🚀 Deployment & Scaling (THIS is what you're missing)

👉 Your Azure / Docker / scaling content belongs here

---

# 🧱 What you SHOULD add (clean version)

Below is a **production-ready cleaned section** you can append to your guide:

---

# 🚀 Deployment & Scaling Guide (Production Ready)

This section explains how to deploy and scale the shared Temporal worker architecture across:

* Local development
* Docker runtime
* Docker Compose scaling
* Azure Container Apps (production)

---

# 🐳 1. Container Build & Registry

## Build image

```bash
docker build -t ghcr.io/<org>/temporal-worker:latest .
```

---

## Push to registry

```bash
docker push ghcr.io/<org>/temporal-worker:latest
```

---

# 🧪 2. Local Execution (Development)

```bash
docker run --rm -it \
  -e TEMPORAL_HOST=localhost:7233 \
  -e TASK_QUEUE=shared-task-queue \
  ghcr.io/<org>/temporal-worker:latest
```

---

# ⚙️ 3. Docker Compose (Multi-Worker Local Scaling)

## Key idea:

> Each container = stateless worker replica

---

## docker-compose.yml

```yaml
version: "3.9"

services:

  worker:
    image: ghcr.io/<org>/temporal-worker:latest
    environment:
      TEMPORAL_HOST: host.docker.internal:7233
      TASK_QUEUE: shared-task-queue
    restart: unless-stopped
```

---

## Scale workers

```bash
docker compose up -d --scale worker=3
```

✔ This gives:

* 3 worker replicas
* same queue
* automatic load balancing

---

# ☁️ 4. Azure Container Apps Deployment

## 🧠 Design principle

> Each Container App = stateless worker pool for a task queue

---

## Payments Worker

```bash
az containerapp create \
  --name temporal-worker-payments \
  --resource-group rg-temporal \
  --environment aca-env \
  --image ghcr.io/<org>/temporal-worker:latest \
  --ingress internal \
  --env-vars \
    TASK_QUEUE=payments-task-queue \
    TEMPORAL_HOST=<temporal-host>
```

---

## Invoice Worker

```bash
az containerapp create \
  --name temporal-worker-invoice \
  --resource-group rg-temporal \
  --environment aca-env \
  --image ghcr.io/<org>/temporal-worker:latest \
  --ingress internal \
  --env-vars \
    TASK_QUEUE=invoice-task-queue \
    TEMPORAL_HOST=<temporal-host>
```

---

## CRM Worker

```bash
az containerapp create \
  --name temporal-worker-crm \
  --resource-group rg-temporal \
  --environment aca-env \
  --image ghcr.io/<org>/temporal-worker:latest \
  --ingress internal \
  --env-vars \
    TASK_QUEUE=crm-task-queue \
    TEMPORAL_HOST=<temporal-host>
```

---

# 📈 5. Scaling Strategy

## Horizontal scaling (preferred)

### Docker Compose

```bash
docker compose up --scale worker=5
```

### Azure Container Apps

```bash
az containerapp update \
  --name temporal-worker-payments \
  --min-replicas 2 \
  --max-replicas 10
```

---

# 🔁 6. Failure Recovery Model

## Worker crash

* replicas continue processing
* no workflow loss
* Temporal reassigns tasks automatically

---

## Deployment rollback

* old workers stop polling
* new workers resume from last state
* workflows remain intact in Temporal server

---

# 🧠 Key Production Principles

## ✔ Stateless workers

Workers must NEVER store state locally

---

## ✔ Shared queue = scaling layer

Queue does NOT cause coupling — workers do

---

## ✔ Scaling unit = worker replica

Not workflow type, not activity type

---

# ⚠️ Important correction to your current draft

Your current version mixes:

❌ architecture
❌ runtime
❌ deployment
❌ scaling
❌ dev commands

👉 This makes it hard to maintain in real teams

---

# 🧭 Recommended final doc structure

Your final guide should be:

```text
1. Architecture Overview
2. Domain Structure Pattern
3. Developer Guide (add new workflow)
4. Worker Runtime Model
5. Failure & Retry Model (Temporal guarantees)
6. Deployment Guide (Azure + Docker)
7. Scaling Guide (HPA / replicas)
8. Operational Runbook
```

---

# 🧠 Final insight (important)

What you are building is NOT:

> “microservices per workflow”

It is:

> **“domain-modular workflow engine running on a horizontally scalable worker pool”**

That is why:

* Azure Container Apps scaling works well
* Docker replicas work well
* shared queue is safe
* isolation is logical, not infra-based

---
# 🚀 Deployment & Scaling Guide (Shared Task Queue Pattern)

This version assumes:

> ✔ ONE task queue for all domains
> ✔ Multiple workflows + activities in same worker runtime
> ✔ Scaling is done via worker replicas, NOT queue splitting

---

# 🧠 Core Principle (IMPORTANT)

> The task queue is NOT a domain boundary.

In this design:

* `shared-task-queue` is the only queue
* routing happens via **workflow type inside Temporal**
* isolation happens via **code modules + worker replicas**

---

# 🐳 1. Container Build & Registry

```bash
docker build -t ghcr.io/<org>/temporal-worker:latest .
```

```bash
docker push ghcr.io/<org>/temporal-worker:latest
```

---

# 🧪 2. Local Execution (Single Shared Queue)

```bash
docker run --rm -it \
  -e TEMPORAL_HOST=localhost:7233 \
  -e TASK_QUEUE=shared-task-queue \
  ghcr.io/<org>/temporal-worker:latest
```

✔ This worker processes:

* Payments workflows
* Invoice workflows
* CRM workflows

ALL from the same queue

---

# ⚙️ 3. Docker Compose (Shared Queue + Horizontal Scaling)

## Key idea

> Scale workers, NOT queues

---

## docker-compose.yml

```yaml
version: "3.9"

services:

  worker:
    image: ghcr.io/<org>/temporal-worker:latest
    environment:
      TEMPORAL_HOST: host.docker.internal:7233
      TASK_QUEUE: shared-task-queue
    restart: unless-stopped
```

---

## Scale workers

```bash
docker compose up -d --scale worker=5
```

✔ Result:

```text
worker-1 → shared-task-queue
worker-2 → shared-task-queue
worker-3 → shared-task-queue
worker-4 → shared-task-queue
worker-5 → shared-task-queue
```

👉 Temporal distributes workflow tasks automatically

---

# ☁️ 4. Azure Container Apps Deployment (SHARED QUEUE ONLY)

## 🧠 Correct design principle

> Multiple replicas of the SAME worker, NOT multiple queues

---

## Payments + Invoice + CRM (single worker pool)

```bash
az containerapp create \
  --name temporal-worker \
  --resource-group rg-temporal \
  --environment aca-env \
  --image ghcr.io/<org>/temporal-worker:latest \
  --ingress internal \
  --env-vars \
    TASK_QUEUE=shared-task-queue \
    TEMPORAL_HOST=<temporal-host>
```

---

# 📈 5. Scaling Strategy (Correct Model)

## ✔ Horizontal scaling (ONLY mechanism needed)

### Docker

```bash
docker compose up --scale worker=10
```

---

### Azure Container Apps

```bash
az containerapp update \
  --name temporal-worker \
  --resource-group rg-temporal \
  --min-replicas 2 \
  --max-replicas 10
```

---

# 🔁 6. Failure Recovery Model (Shared Queue Safe Design)

## ✔ Worker crash

* other replicas continue processing
* no queue loss
* Temporal reassigns tasks automatically

---

## ✔ Deployment update

* old replicas drain naturally
* new replicas pick up tasks immediately
* no workflow interruption

---

## ✔ Domain failure (e.g., CRM bug)

* only CRM workflows fail
* payments + invoice unaffected
* retries handled per workflow

---

# 🧠 7. Correct Mental Model (IMPORTANT)

## ❌ Wrong mental model

```
payments queue
invoice queue
crm queue
```

## ✔ Correct model

```
shared-task-queue
    ├── PaymentWorkflow
    ├── InvoiceWorkflow
    ├── CRMWorkflow
```

Routing happens via:

> workflow type + activity execution mapping (NOT queue separation)

---

# ⚖️ 8. Why this is better than multi-queue design (for your case)

## ✔ Advantages

* single operational surface
* easy scaling (just replicas)
* low infra cost
* easy onboarding
* no queue fragmentation
* Temporal-native design

---

## ❌ When multi-queue becomes needed

Only when:

* different SLAs (ms vs hours)
* compliance separation required
* extremely high throughput domains
* different security boundaries

---

# 🧭 9. Correct Production Architecture

```text
                Temporal Server
                       │
             shared-task-queue
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Worker replica  Worker replica  Worker replica
        │              │              │
        └────── domain-modular workflows ──────┘
```

---

# 🧠 Final correction (important)

Your earlier version accidentally implied:

> “queue per domain = isolation”

That is NOT required in Temporal.

In your chosen architecture:

> ✔ isolation comes from workflow logic
> ✔ scalability comes from worker replicas
> ✔ queue is just a routing buffer

---

# 🚀 One-line final takeaway

> **You scale Temporal by adding workers, not by multiplying queues or containers per domain.**

---
# 🧠 What “blue/green workers” means in Temporal

Blue/green in Temporal workers is a bit different from web apps, because **workers don’t receive traffic directly**—they *compete for tasks from a queue*. So the rollout strategy is about controlling **which worker version is polling the queue**, not switching a load balancer.

---
You run two parallel worker fleets:

* 🔵 **Blue = current production version**
* 🟢 **Green = new version**

Both:

* connect to the **same Temporal cluster**
* poll the **same task queue**
* execute workflows/activities independently

Key idea:

> Temporal safely decouples execution from deployment because state lives in the server, not in workers.

---

# 🏗 Architecture

```text
                shared-task-queue
                        │
        ┌───────────────┴───────────────┐
        │                               │
   🔵 BLUE workers                 🟢 GREEN workers
   (v1 code)                      (v2 code)
        │                               │
   stable execution              new logic rollout
```

---

# 🚀 Why this works safely in Temporal

Temporal guarantees:

* Workflow state is persisted in the server
* Activities are retryable
* Workers are stateless executors
* Tasks are re-dispatched if a worker disappears

So:

> You can safely add/remove worker versions without losing workflow progress.

---

# 🔁 Safe Blue/Green Deployment Strategy

## STEP 1 — Deploy GREEN workers (no traffic cutover yet)

```bash
docker run -d \
  --name worker-green \
  -e WORKER_VERSION=green \
  -e TASK_QUEUE=shared-task-queue \
  ghcr.io/app/temporal-worker:v2
```

Now:

* BLUE still processes everything
* GREEN starts polling in parallel

👉 Both are active simultaneously

---

## STEP 2 — Observe dual execution

You now monitor:

* success rate
* retry patterns
* latency
* activity failures
* workflow completion correctness

If GREEN is buggy:

* only GREEN executions fail
* BLUE continues normally

---

## STEP 3 — Gradual traffic shift (important nuance)

Temporal doesn’t “route traffic”, but you can bias execution using:

### Option A — Scale weighting (most common)

```bash
# Blue: 3 replicas
# Green: 1 replica
```

Then gradually shift:

| Stage | Blue | Green |
| ----- | ---- | ----- |
| 1     | 3    | 1     |
| 2     | 2    | 2     |
| 3     | 1    | 3     |
| 4     | 0    | 4     |

👉 This is effectively traffic shifting

---

### Option B — Task queue split (advanced)

Only if needed:

* `shared-task-queue-v1`
* `shared-task-queue-v2`

But this breaks your “single queue design”, so avoid unless necessary.

---

## STEP 4 — Validation window

Before full cutover:

Check:

* workflow completion rate
* error rate per activity
* retry storms
* external API stability

If GREEN is bad:

👉 simply scale it down to 0

No rollback complexity.

---

## STEP 5 — Full cutover

Once GREEN is stable:

```bash
docker stop worker-blue
```

Now only GREEN remains active.

---

# 🔄 Rollback Strategy (this is where Temporal shines)

If GREEN breaks:

* stop GREEN workers
* BLUE still has workflow state continuity
* Temporal reassigns pending tasks automatically

No:

* data loss
* workflow restart
* manual replay

---

# ⚠️ Important Temporal-specific insight

Unlike microservices:

> Workers are **replaceable executors**, not state owners

So rollback is NOT:

* database rollback
* traffic switching
* request rerouting

It is simply:

> “stop bad workers, start good workers”

---

# 🧩 Best practice rollout pattern

## 1. Shadow mode (optional but powerful)

GREEN runs but does NOT execute side effects:

* no DB writes
* no external calls
* only logs results

Used for validation.

---

## 2. Canary workers

Start with:

* 1–5% of capacity on GREEN

---

## 3. Full rollout

Scale GREEN to 100%

---

# 📊 Recommended production setup

```text
Blue workers: stable version (always running)
Green workers: new version (gradual rollout)

Both poll same queue
Scaling controls exposure
```

---

# 🚨 Common mistakes (very important)

## ❌ Mistake 1: thinking queue controls routing

Temporal does NOT route by version.

---

## ❌ Mistake 2: deploying green without blue

No safety net.

---

## ❌ Mistake 3: shared mutable dependencies

Both versions must be compatible with:

* workflow history
* activity signatures

Otherwise replay failures happen.

---

# 🧠 Key mental model

> Blue/green in Temporal is not traffic switching.
> It is **worker fleet version control over a shared execution stream**.

---

# 🧭 One-line summary

> You safely deploy new Temporal worker versions by running them in parallel with the old version, gradually scaling replicas while both consume the same task queue, then retiring the old workers once stability is confirmed.

---
# 🧠 how to avoid breaking running workflows during code changes in Temporal
This is one of the most important (and most misunderstood) parts of Temporal.

If you get this wrong, you don’t get “deployment bugs”—you get **workflow replay failures, stuck executions, or corrupted execution history interpretation**.
> **Running workflows execute based on recorded history, not current code.**

That single fact is what protects you—but also what breaks systems if you ignore compatibility.

---

# 💥 What actually breaks running workflows during code changes?

There are 3 main failure modes:

---

## ❌ 1. Changing workflow logic (determinism break)

Example:

```python
if amount > 100:
    approve()
else:
    reject()
```

You change it to:

```python
if amount > 200:
    approve()
```

### Problem:

Old workflows replay history using new code → decisions no longer match recorded history.

👉 Result:

* “Non-deterministic workflow error”
* workflow stuck
* replay failure

---

## ❌ 2. Changing activity signature

Old workflow expects:

```python
charge_payment(amount, currency)
```

You change to:

```python
charge_payment(amount, currency, region)
```

👉 Result:

* workflow cannot replay activity invocation
* execution failure

---

## ❌ 3. Removing or renaming activities/workflows

If history contains:

* `validate_payment_v1`

and you delete it:

👉 workflow cannot reconstruct execution

---

# 🛡️ The real solution: 4-layer compatibility strategy

---

# 1. ✔ Never break workflow determinism (Golden Rule)

## Safe rule:

> Workflow code must behave like a pure function of history.

### Allowed:

* refactoring internal variables
* improving structure
* extracting helper functions

### NOT allowed:

* changing decision logic on existing paths
* changing branching conditions for past events

---

# 2. ✔ Use versioned workflows (Temporal’s built-in safety mechanism)

## Pattern:

```python id="v1"
@workflow.defn(name="PaymentWorkflow")
class PaymentWorkflowV1:
    ...
```

New version:

```python id="v2"
@workflow.defn(name="PaymentWorkflowV2")
class PaymentWorkflowV2:
    ...
```

### Then:

* old workflows continue on V1
* new workflows start on V2

👉 NO replay conflicts

---

# 3. ✔ Use `workflow.get_version()` for safe evolution

This is the MOST IMPORTANT tool.

## Example:

```python id="ver1"
from temporalio import workflow

@workflow.defn
class PaymentWorkflow:

    @workflow.run
    async def run(self, payload):

        version = workflow.get_version(
            change_id="payment-logic-v2",
            min_supported=1,
            max_supported=2,
        )

        if version == 1:
            if payload["amount"] > 100:
                result = "approved"
            else:
                result = "rejected"

        else:
            if payload["amount"] > 200:
                result = "approved"
            else:
                result = "rejected"

        return {"result": result}
```

---

## Why this works

* old executions replay with version = 1
* new executions use version = 2
* no history mismatch

---

# 4. ✔ Activity compatibility rules (VERY IMPORTANT)

Activities are easier than workflows, but still dangerous.

---

## Safe changes:

✔ Add optional fields
✔ Improve internal logic
✔ Optimize performance
✔ Add logging

---

## Unsafe changes:

❌ Remove arguments
❌ Change argument order
❌ Rename activity
❌ Change return schema without fallback

---

## Safe evolution pattern:

```python id="actv1"
@activity.defn
async def charge_payment(amount: float, currency: str, region: str = "AU"):
```

👉 Always use:

* default values
* backward-compatible signatures

---

# 🧩 5. Use “wrapper activities” for evolution (best practice)

Instead of breaking old activity:

```python id="wrap1"
@activity.defn
async def charge_payment_v2(payload):
    return charge_payment_legacy(payload)
```

---

# 6. ✔ Safe deployment pattern (NO workflow break)

## Step-by-step rollout:

### STEP 1 — Add new code (do NOT remove old)

* introduce V2 workflows OR version flags
* keep V1 intact

---

### STEP 2 — Deploy workers with both versions

* old + new coexist
* same task queue

---

### STEP 3 — Let old workflows finish naturally

Important:

> Running workflows are NOT restarted

They continue using old logic snapshot

---

### STEP 4 — Stop old version ONLY after drain

* ensure no active executions exist
* then remove V1 safely

---

# ⚠️ 7. What NOT to do (common production mistakes)

## ❌ Never do this:

* rename workflow class in place
* remove activity without versioning
* change branching logic without get_version()
* assume “redeploy fixes everything”

---

# 🧠 Mental model that prevents 90% of bugs

> Workflow code = immutable interpretation engine for historical event log

So:

* history is truth
* code is interpreter
* mismatch = failure

---

# 🔥 Enterprise-grade evolution strategy (what Fortune 500 actually do)

They combine:

## 1. Versioned workflows

## 2. Feature flags inside workflows

## 3. Backward-compatible activities

## 4. Gradual worker rollout (blue/green)

## 5. Long-running workflow isolation policies

---

# 🧭 Final summary

To avoid breaking running workflows:

### ✔ DO

* use `workflow.get_version()`
* keep workflow deterministic
* keep activity backward compatible
* introduce new workflow versions instead of modifying old ones
* deploy blue/green workers safely

### ❌ DO NOT

* change workflow logic in-place
* rename or remove activities
* break replay determinism assumptions

---

# 🚀 One-line takeaway

> In Temporal, you don’t “update workflows”—you **evolve them safely through versioning while old executions continue replaying the original code path unchanged.**
