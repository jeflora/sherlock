from typing import Optional
from fastapi import APIRouter
import time

import app.alarms.mongo_manager as mongo

router = APIRouter()


MIN_NANO_SECS = 60_000_000_000


@router.get("/alarms", tags=["alarms"])
async def get_alarms(
    model_id: Optional[str] = "",
    app_name: Optional[str] = "",
    service_name: Optional[str] = "",
    last_minutes: Optional[int] = -1,
):
    in_params = [model_id, app_name, service_name]
    in_filters = ["model_id", "app_name", "service_name"]
    filters = [{fit: par} for par, fit in zip(in_params, in_filters) if par != ""]

    if last_minutes > 0:
        filters.append(
            {"interval_start": {"$gte": time.time_ns() - last_minutes * MIN_NANO_SECS}}
        )

    alarms = [a for a in mongo.list_alarms(filters)]
    for alarm in alarms:
        alarm["_id"] = str(alarm["_id"])

    return alarms


@router.get("/alarms/plot", tags=["alarms"])
async def get_alarms_to_plot(
    last_timestamp: int,
    app_name: Optional[str] = "",
    service_name: Optional[str] = "",
):
    return mongo.list_grouped_alarms(last_timestamp, app_name, service_name)
