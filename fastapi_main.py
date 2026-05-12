import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from temporalio.client import Client


# =====================================================
# CONFIG
# =====================================================
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "shared-task-queue"

app = FastAPI(title="Temporal API Gateway")

client: Client = None


# =====================================================
# REQUEST MODELS
# =====================================================

class PaymentRequest(BaseModel):
    payment_id: str
    customer_id: str
    amount: float
    currency: str = "AUD"


class InvoiceRequest(BaseModel):
    customer_id: str
    amount: float


class CRMRequest(BaseModel):
    customer_id: str
    action: str


# =====================================================
# WORKFLOW REGISTRY
# =====================================================
WORKFLOW_TYPES = {
    "payment": "PaymentWorkflow",
    "invoice": "InvoiceWorkflow",
    "crm": "CRMWorkflow",
}


# =====================================================
# INIT TEMPORAL CLIENT
# =====================================================
@app.on_event("startup")
async def startup():
    global client
    client = await Client.connect(TEMPORAL_HOST)
    print("✅ Connected to Temporal")


# =====================================================
# GENERIC WORKFLOW STARTER
# =====================================================
async def start_workflow(workflow_name: str, workflow_id: str, payload: dict):

    if client is None:
        raise RuntimeError("Temporal client not initialized")

    return await client.start_workflow(
        workflow_name,
        payload,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )


# =====================================================
# PAYMENT WORKFLOW API
# =====================================================
@app.post("/payment")
async def payment(req: PaymentRequest):
    """
    PAYMENT WORKFLOW EXAMPLE:

    {
        "payment_id": "pay_1001",
        "customer_id": "cust_12345",
        "amount": 250.75,
        "currency": "AUD"
    }
    """

    workflow_id = f"payment-{req.payment_id}-{uuid.uuid4()}"

    return await start_workflow(
        WORKFLOW_TYPES["payment"],
        workflow_id,
        req.model_dump()
    )


# =====================================================
# INVOICE WORKFLOW API
# =====================================================
@app.post("/invoice")
async def invoice(req: InvoiceRequest):
    """
    INVOICE WORKFLOW EXAMPLE:

    {
        "customer_id": "cust_12345",
        "amount": 1200.50
    }
    """

    workflow_id = f"invoice-{req.customer_id}-{uuid.uuid4()}"

    return await start_workflow(
        WORKFLOW_TYPES["invoice"],
        workflow_id,
        req.model_dump()
    )


# =====================================================
# CRM WORKFLOW API
# =====================================================
@app.post("/crm")
async def crm(req: CRMRequest):
    """
    CRM WORKFLOW EXAMPLE:

    {
        "customer_id": "cust_12345",
        "action": "churn_analysis"
    }
    """

    workflow_id = f"crm-{req.customer_id}-{req.action}-{uuid.uuid4()}"

    return await start_workflow(
        WORKFLOW_TYPES["crm"],
        workflow_id,
        req.model_dump()
    )


# ------------------------------------------------
# Run FastAPI
# ------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)