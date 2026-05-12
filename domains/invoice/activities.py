import asyncio
from temporalio import activity


@activity.defn
async def generate_invoice(payload: dict) -> dict:
    print("[INVOICE] generate_invoice")
    await asyncio.sleep(1)

    return {
        "invoice_id": f"INV-{payload['customer_id']}",
        "amount": payload["amount"]
    }


@activity.defn
async def send_invoice(payload: dict) -> dict:
    print("[INVOICE] send_invoice")
    await asyncio.sleep(1)

    return {"sent": True}