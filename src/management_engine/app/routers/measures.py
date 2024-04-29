from http import HTTPStatus
from fastapi import APIRouter, HTTPException
import requests, datetime

import app.mongo.mongo_manager as mongo


router = APIRouter()

LAST_MINUTES = 10
SOFT_REACTION_THRESHOLD = 5
AGGRESSIVE_REACTION_THRESHOLD = 2 * SOFT_REACTION_THRESHOLD


async def is_passive_measure(app_name: str, service_name: str):
    services = mongo.list_app_services(
        mongo.get_cluster_name_from_app_name(app_name), app_name
    )

    for service in services:
        if service.get("name", "") == service_name:
            return service.get("passive_measure", True)

    return True


async def restart_service_measure(app_name: str, service_name: str):
    cluster_name = mongo.get_cluster_name_from_app_name(app_name)
    app_details = mongo.list_app_details(cluster_name, app_name)

    resp = requests.post(
        f"http://k8s_daemon/{cluster_name}/measures/restart/{service_name}",
        json={"namespace": app_details["namespace"]},
    )

    return resp.status_code < 400


async def move_service_measure(app_name: str, service_name: str):
    cluster_name = mongo.get_cluster_name_from_app_name(app_name)
    cluster_details = mongo.get_cluster_from_name(cluster_name)
    app_details = mongo.list_app_details(cluster_name, app_name)

    resp = requests.post(
        f"http://k8s_daemon/{cluster_name}/measures/move/{service_name}",
        json={
            "namespace": app_details.get("namespace", ""),
            "node_taints": cluster_details.get("node_taints", []),
        },
    )

    return resp.status_code < 400


@router.post("/measures/reactive/{model_id}", tags=["measures", "reactive"])
async def apply_reactive_measure(model_id: str):
    model_details = mongo.list_model(model_id)
    if not model_details:
        return {"model_id": model_id, "measure": None}

    app_name = model_details.app_name
    service_name = model_details.service

    measures = [
        {
            "name": "move",
            "func": move_service_measure,
            "threshold": AGGRESSIVE_REACTION_THRESHOLD,
        },
        {
            "name": "restart",
            "func": restart_service_measure,
            "threshold": SOFT_REACTION_THRESHOLD,
        },
    ]
    mongo.add_reactive_measure(model_id)
    last_action = mongo.get_last_action(model_id)

    now = datetime.datetime.now()
    minutes_since_last_action = int(
        round(
            (
                now - last_action.get("acted_at", now) if last_action else now
            ).total_seconds()
            / 60.0,
            0,
        )
    )

    filter_minutes = (
        LAST_MINUTES
        if minutes_since_last_action == 0
        else min(minutes_since_last_action, LAST_MINUTES)
    )

    count = mongo.count_reactive_measures(model_id, last_minutes=filter_minutes)
    if await is_passive_measure(app_name, service_name) or count == 0:
        return {"model_id": model_id, "measure": None}

    measure_to_apply = None
    for measure in measures:
        if count % measure["threshold"] == 0:
            measure_to_apply = measure
            break

    if not measure_to_apply:
        return {"model_id": model_id, "measure": None}

    await measure_to_apply["func"](app_name, service_name)
    mongo.add_reactive_measure_execution(
        measure_to_apply["name"], model_id, app_name, service_name
    )

    return {"model_id": model_id, "measure": measure_to_apply["name"].lower()}


@router.post("/measures/proactive/{model_id}", tags=["measures", "proactive"])
async def apply_proactive_measure(model_id: str):
    pass
    # TODO: Stop running detection model

    # TODO: Start new version detection model ...
