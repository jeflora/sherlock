from fastapi import APIRouter, Request
from typing import Optional, List, Union, Dict
from pydantic import BaseModel
from app.daemon.daemonclient import DaemonClient
import os, requests, time
from http import HTTPStatus

import app.routers.monitoring as monitoring


class ReqBody(BaseModel):
    ttime: int = 0
    # Algorithm data
    algo_name: str
    algo_params: Dict
    service_name: str


router = APIRouter()

daemon_client = DaemonClient(os.getenv("DAEMON_HOST"), os.getenv("DAEMON_PORT"))


@router.get("/intrusion/models", tags=["intrusion", "models"])
async def get_models(app_name: Optional[str] = ""):
    cluster_apps = {}
    param = "" if not app_name else f"?app_name={app_name}"
    resp = requests.get(f"http://management_engine/models{param}")
    models = resp.json() if resp.status_code < 400 else {}

    if app_name != "":
        resp = requests.get(f"http://management_engine/cluster/{app_name}")
        cluster_apps[app_name] = (
            resp.json().get("name", "") if resp.status_code < 400 else ""
        )

    for model in models:
        app_name = model.get("app_name", None)

        if not app_name:
            continue

        if app_name not in cluster_apps.keys():
            resp = requests.get(f"http://management_engine/cluster/{app_name}")
            cluster_apps[app_name] = (
                resp.json().get("name", "") if resp.status_code < 400 else ""
            )

        model["cluster_name"] = cluster_apps[app_name]

    return models


@router.get("/intrusion/model/{model_id}", tags=["intrusion", "models"])
async def get_model_status(model_id: str):
    resp = requests.get(f"http://management_engine/model/{model_id}")
    return resp.json() if resp.status_code < 400 else {}


@router.delete("/intrusion/model/{model_id}", tags=["intrusion", "models"])
async def delete_detection_model(model_id: str):
    resp = requests.delete(f"http://management_engine/model/{model_id}")
    return resp.json() if resp.status_code < 400 else {}


# @router.get("/intrusion/training/models/{app_name}", tags=["intrusion", "training"])
# async def get_models_training_status(app_name: str):
#     resp = requests.get(f"http://management_engine/training/models/{app_name}")
#     return resp.json() if resp.status_code < 400 else {}


class BasicDet(BaseModel):
    ttime: int = -1  # run forever


class TrainModel(BaseModel):
    staging: bool = False
    reading_ch: str = ""
    ttime: int = 10  # minutes
    nreplicas: int = 1


async def get_app_monitoring_filters(app_name: str):
    resp = requests.get(f"http://management_engine/cluster/app_details/{app_name}")
    if not resp or not resp.json().get("monitor_filters", ""):
        return []

    mon_filters = resp.json().get("monitor_filters", "")
    if not mon_filters:
        return []

    return [mon_filters]


@router.post(
    "/intrusion/training/{app_name}/{service_name}", tags=["intrusion", "training"]
)
async def start_model_training(app_name: str, service_name: str, body: TrainModel):
    """
    Train a detection model with data coming from the cluster.
    The algorithms and monitoring configuration come from the data previously provided.

    **app_name**: the name id of the application to which the service belongs

    **service_name**: the name id of the service whose model is to be trained

    **ttime**: (minutes) time to run the training phase (default is 10min)
    """
    params = monitoring.MonRequest(
        monitor_filters=await get_app_monitoring_filters(app_name)
    )
    resp = await monitoring.start_monitoring_app(app_name, params)
    if not resp or resp.get("status") != "in_progress":
        return {}

    resp = requests.post(
        f"http://management_engine/automation/training/{app_name}/{service_name}",
        json=body.model_dump(),
    )

    return (
        {}
        if resp.status_code not in [HTTPStatus.OK, HTTPStatus.ACCEPTED]
        else resp.json()
    )


@router.post(
    "/intrusion/training/{app_name}", tags=["intrusion", "training"], deprecated=True
)
async def start_model_training(
    app_name: str, req: Request, body: ReqBody, namespace: Optional[str] = "default"
):
    return {}
    req_data = await req.json()

    # Monitoring Status | Start if not running...
    resp = await monitoring.status_monitoring_app(app_name, namespace=namespace)
    if not resp or resp.get("status") != "in_progress":
        resp = await monitoring.start_monitoring_app(app_name, namespace)
        if not resp or resp.get("status") != "in_progress":
            return {}

    req_data["app_name"] = app_name
    req_data["nreplicas"] = daemon_client.get_service_nreplicas(body.service_name)
    req_data["mon_params"] = daemon_client.get_monitoring_params()
    req_data["docker_image"] = daemon_client.get_service_docker_image(body.service_name)
    resp = requests.post(
        f"http://management_engine/training/{app_name}",
        json=req_data,
    )
    if resp.status_code not in [HTTPStatus.OK, HTTPStatus.ACCEPTED]:
        return {}

    return resp.json()


@router.delete("/intrusion/training/{model_id}", tags=["intrusion", "training"])
async def abort_model_training(model_id: str):
    resp = requests.delete(f"http://management_engine/training/{model_id}")
    return resp.json() if resp.status_code < 400 else {}


# @router.get("/intrusion/detection/models/{app_name}", tags=["intrusion", "detection"])
# async def get_models_detection_status(app_name: str):
#     resp = requests.get(f"http://management_engine/detection/models/{app_name}")
#     return resp.json() if resp.status_code < 400 else {}


@router.post(
    "/intrusion/detection/{app_name}/{model_id}", tags=["intrusion", "detection"]
)
async def start_detection_model(
    app_name: str,
    model_id: str,
    body: BasicDet,
):
    # Monitoring Status | Start if not running...
    params = monitoring.MonRequest(
        monitor_filters=await get_app_monitoring_filters(app_name)
    )
    resp = await monitoring.start_monitoring_app(app_name, params)
    if not resp or resp.get("status") != "in_progress":
        return {}

    ttime = body.ttime
    req_data = {
        "mon_params": daemon_client.get_monitoring_params(),
        "ttime": ttime,
    }
    resp = requests.post(
        f"http://management_engine/detection/{model_id}",
        json=req_data,
    )

    return resp.json() if resp.status_code < 400 else {}


@router.delete("/intrusion/detection/{model_id}", tags=["intrusion", "detection"])
async def stop_detection_model(model_id: str):
    resp = requests.delete(f"http://management_engine/detection/{model_id}")
    return resp.json() if resp.status_code < 400 else {}
