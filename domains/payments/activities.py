import asyncio
import uuid
from temporalio import activity


@activity.defn
async def validate_payment(payload: dict) -> dict:
    print("[PAYMENT] validate_payment")

    await asyncio.sleep(1)

    if payload["amount"] <= 0:
        return {"approved": False, "reason": "invalid amount"}

    return {"approved": True}


@activity.defn
async def charge_payment(payload: dict) -> dict:
    print("[PAYMENT] charge_payment")

    await asyncio.sleep(2)

    return {
        "transaction_id": str(uuid.uuid4()),
        "status": "charged"
    }