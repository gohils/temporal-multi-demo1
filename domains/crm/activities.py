import asyncio
from temporalio import activity


@activity.defn
async def update_customer(payload: dict) -> dict:
    print("[CRM] update_customer")
    await asyncio.sleep(1)

    return {"customer_updated": True}


@activity.defn
async def sync_salesforce(payload: dict) -> dict:
    print("[CRM] sync_salesforce")
    await asyncio.sleep(2)

    return {"salesforce": "synced"}