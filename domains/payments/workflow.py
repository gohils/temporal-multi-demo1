from temporalio import workflow
from datetime import timedelta
from .activities import validate_payment, charge_payment


@workflow.defn
class PaymentWorkflow:

    @workflow.run
    async def run(self, payload: dict):

        res = await workflow.execute_activity(
            validate_payment,
            payload,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not res["approved"]:
            return {"status": "DECLINED"}

        charge = await workflow.execute_activity(
            charge_payment,
            payload,
            start_to_close_timeout=timedelta(seconds=20),
        )

        return {"status": "SUCCESS", "tx": charge["transaction_id"]}