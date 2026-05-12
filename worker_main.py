import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from domains.payments.workflow import PaymentWorkflow
from domains.invoice.workflow import InvoiceWorkflow
from domains.crm.workflow import CRMWorkflow

from domains.payments.activities import *
from domains.invoice.activities import *
from domains.crm.activities import *

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal-server-demo.australiaeast.cloudapp.azure.com:7233")
# TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "shared-task-queue"


async def main():

    print("\n🚀 STARTING SHARED TEMPORAL WORKER")
    print(f"Connecting to: {TEMPORAL_HOST}\n")

    client = await Client.connect(TEMPORAL_HOST)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,

        # 3 workflows in same worker
        workflows=[
            PaymentWorkflow,
            InvoiceWorkflow,
            CRMWorkflow,
        ],

        # all activities from all domains
        activities=[
            # payment
            validate_payment,
            charge_payment,

            # invoice
            generate_invoice,
            send_invoice,

            # crm
            update_customer,
            sync_salesforce,
        ],

        max_concurrent_workflow_tasks=20,
        max_concurrent_activities=50,
    )

    print("🟢 Worker running on shared queue...\n")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())