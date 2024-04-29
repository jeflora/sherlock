from fastapi import APIRouter
from typing import Annotated, List
from annotated_types import Len
from pydantic import BaseModel

import os, requests, asyncio
from http import HTTPStatus

from app.daemon.daemonclient import DaemonClient


router = APIRouter()

daemon_client = DaemonClient(os.getenv("DAEMON_HOST"), os.getenv("DAEMON_PORT"))


class MonRequest(BaseModel):
    monitor_filters: Annotated[List[str], Len(min_length=1)]
    node_taints: List[str] = []


async def get_namespace_from_app_name(app_name: str):
    resp = requests.get(f"http://management_engine/cluster/app_details/{app_name}")
    if not resp or not resp.json().get("namespace", ""):
        return {}

    return resp.json().get("namespace", "")


@router.post("/monitoring/{app_name}", tags=["monitoring"])
async def start_monitoring_app(app_name: str, body: MonRequest):
    resp = await status_monitoring_app(app_name)
    if resp and resp.get("status") == "in_progress":
        return resp

    resp = requests.post(
        f"http://monitor_agent/monitoring/init_data_receiver/{app_name}"
    )
    if resp.status_code not in [HTTPStatus.OK, HTTPStatus.ACCEPTED]:
        return {}

    trace = resp.json()
    resp = requests.get(f"http://management_engine/cluster/{app_name}")
    if resp.status_code != HTTPStatus.OK:
        return {}

    cluster_name = resp.json().get("name", "")
    if not cluster_name:
        return {}

    namespace = await get_namespace_from_app_name(app_name)
    if not namespace:
        return {}

    resp = daemon_client.start_data_collection(
        cluster_name, app_name, namespace, body.monitor_filters, body.node_taints
    )
    if not resp:
        await asyncio.sleep(2)
        resp = requests.delete(
            f"http://monitor_agent/monitoring/data_receiver/{app_name}"
        )
        return {}

    return trace


@router.get("/monitoring/status/{app_name}", tags=["monitoring"])
async def status_monitoring_app(app_name: str):
    resp = requests.get(f"http://monitor_agent/monitoring/status/{app_name}")
    return resp.json() if resp.status_code < 400 else {}


@router.delete("/monitoring/{app_name}", tags=["monitoring"])
async def stop_monitoring_app(app_name: str):
    # Calling close on daemon will close receiver
    resp = requests.get(f"http://management_engine/cluster/{app_name}")
    if resp.status_code != HTTPStatus.OK:
        return {}

    namespace = await get_namespace_from_app_name(app_name)
    if not namespace:
        return {}

    cluster_name = resp.json().get("name", "")
    return daemon_client.close_data_collection(cluster_name, app_name, namespace)
