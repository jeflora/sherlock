from fastapi import APIRouter
from typing import Optional
from app.daemon.daemonclient import DaemonClient
import os, requests


router = APIRouter()
daemon_client = DaemonClient(os.getenv("DAEMON_HOST"), os.getenv("DAEMON_PORT"))


@router.get("/traces/", tags=["traces"])
def list_traces_available(cluster_name: Optional[str] = None):
    resp = requests.get(
        f"http://monitor_agent/traces",
        params={} if not cluster_name else {"cluster_name": cluster_name},
    )
    traces = resp.json() if resp.status_code < 400 else []
    cluster_apps = {}
    for trace in traces:
        app_name = trace.get("app_name", None)

        if not app_name:
            continue

        if cluster_name is not None:
            cluster_apps[app_name] = cluster_name

        if app_name not in cluster_apps.keys():
            resp = requests.get(f"http://management_engine/cluster/{app_name}")
            cluster_apps[app_name] = (
                resp.json().get("name", "") if resp.status_code < 400 else ""
            )

        trace["cluster_name"] = cluster_apps[app_name]

    return traces


@router.delete("/traces/{id}", tags=["traces"])
def delete_trace(id: int):
    resp = requests.delete(f"http://monitor_agent/traces/{id}")
    return resp.json() if resp.status_code < 400 else {}
