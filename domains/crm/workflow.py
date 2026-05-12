from temporalio import workflow
from datetime import timedelta
from .activities import update_customer, sync_salesforce


@workflow.defn
class CRMWorkflow:

    @workflow.run
    async def run(self, payload: dict):

        await workflow.execute_activity(
            update_customer,
            payload,
            start_to_close_timeout=timedelta(seconds=10),
        )

        await workflow.execute_activity(
            sync_salesforce,
            payload,
            start_to_close_timeout=timedelta(seconds=20),
        )

        return {"status": "CRM_UPDATED"}