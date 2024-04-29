import datetime, random
from fastapi import APIRouter
from typing import Optional
import requests


router = APIRouter()


@router.get("/alarms", tags=["alarms"])
async def get_alarms(
    model_id: Optional[str] = "",
    app_name: Optional[str] = "",
    service_name: Optional[str] = "",
):
    in_params = [model_id, app_name, service_name]
    in_filters = ["model_id", "app_name", "service_name"]
    filters = {fit: par for par, fit in zip(in_params, in_filters) if par != ""}

    return requests.get("http://detection_model_manager/alarms", params=filters).json()


@router.get("/alarms/plot", tags=["alarms"])
async def get_alarms_to_plot(
    cluster_name: Optional[str] = "",
    app_name: Optional[str] = "",
    service_name: Optional[str] = "",
    last_timestamp: Optional[int] = -1,
):
    now = datetime.datetime.now()
    now_ts = int(now.timestamp())
    in_params = [cluster_name, app_name, service_name]
    in_filters = ["cluster_name", "app_name", "service_name"]
    filters = {fit: par for par, fit in zip(in_params, in_filters) if par != ""}

    filters["last_timestamp"] = (
        last_timestamp
        if last_timestamp != -1
        else int((now - datetime.timedelta(minutes=1, seconds=30)).timestamp())
    )

    alarms = requests.get(
        "http://detection_model_manager/alarms/plot", params=filters
    ).json()

    return [
        {
            "timestamp": i,
            "alarms": alarms.get(str(i), 0),
        }
        for i in range(filters["last_timestamp"], now_ts + 1)
    ]
