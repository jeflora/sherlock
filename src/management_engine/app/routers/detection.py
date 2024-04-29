from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import requests

import app.mongo.mongo_manager as mongo
import app.processing.utils as utils


router = APIRouter()


@router.get("/detection/models/{app_name}", tags=["detection"])
async def get_models_detection_status(
    app_name: str, namespace: Optional[str] = "default"
):
    return mongo.list_models([{"app_name": app_name}])


@router.post("/detection/{model_id}", tags=["detection"])
async def start_detection_model(model_id: str, request: Request):
    req_params = ["mon_params", "ttime"]
    if not await request.body():
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Missing params in request body. Params: {','.join(req_params)}",
        )

    request_data = await request.json()
    if not all(k in request_data for k in req_params):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Missing params in request body. Params: {','.join(req_params)}",
        )

    model = mongo.list_model(model_id)
    if not model:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail=f"Model {model_id} not found.")

    algo_resp = requests.get(f"http://detection_model_manager/algorithm/{model.name}")
    if algo_resp.status_code >= 400:
        raise HTTPException(
            algo_resp.status_code, detail=algo_resp.json().get("detail")
        )

    monitoring_params = request_data.get("mon_params")
    resp = requests.post(
        f"http://data_proc_agent/processing/data_processor",
        json={
            "params": monitoring_params,
            "proc_technique": model.data_processing,
            "reading_ch": model.app_name,
            "user_filters": utils.select_data_filters(
                monitoring_params, model.docker_image
            ),
            "ttime": request_data.get("ttime"),
            "index_map_name": algo_resp.json().get("index_map_name"),
        },
    )
    if resp.status_code >= 400:
        raise HTTPException(resp.status_code, detail=resp.json().get("detail"))

    redis_reading_ch = resp.json().get("uid")
    print(redis_reading_ch)
    resp = requests.post(
        f"http://detection_model_manager/detection/{model.get_id()}",
        json={
            "app_name": model.app_name,
            "service_name": model.service,
            "data_rch": redis_reading_ch,
        },
    )
    if resp.status_code >= 400:
        requests.delete(
            f"http://data_proc_agent/processing/data_processor/{redis_reading_ch}"
        )
        raise HTTPException(
            HTTPStatus.SERVICE_UNAVAILABLE, detail="Cannot fulfill request."
        )
    feedback = resp.json()

    model_details = model.get_mongo_dict()
    model_details["_id"] = model.get_id()
    resp = requests.post(
        "http://metrics_engine/metrics/monitor/detection",
        json={
            "model_details": model_details,
            "reading_ch": redis_reading_ch,
        },
    )
    if resp.status_code >= 400:
        requests.delete(f"http://detection_model_manager/detection/{model.get_id()}")
        requests.delete(
            f"http://data_proc_agent/processing/data_processor/{redis_reading_ch}"
        )
        raise HTTPException(
            HTTPStatus.SERVICE_UNAVAILABLE, detail="Cannot fulfill request."
        )

    return feedback


@router.delete("/detection/{model_id}", tags=["detection"])
async def stop_detection_model(model_id: str):
    return requests.delete(
        f"http://detection_model_manager/detection/{model_id}"
    ).json()
