from temporalio import workflow
from datetime import timedelta
from .activities import generate_invoice, send_invoice


@workflow.defn
class InvoiceWorkflow:

    @workflow.run
    async def run(self, payload: dict):

        invoice = await workflow.execute_activity(
            generate_invoice,
            payload,
            start_to_close_timeout=timedelta(seconds=10),
        )

        await workflow.execute_activity(
            send_invoice,
            invoice,
            start_to_close_timeout=timedelta(seconds=10),
        )

        return {"status": "INVOICED", "invoice": invoice}