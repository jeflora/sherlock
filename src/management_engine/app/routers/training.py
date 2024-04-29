from http import HTTPStatus
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import requests

import app.processing.utils as utils
from app.processing.model import Model
import app.mongo.mongo_manager as mongo


router = APIRouter()


class ReqBody(BaseModel):
    app_name: str
    ttime: int = 0
    # Service Data
    service_name: str
    nreplicas: int
    docker_image: str
    # Algorithm Data
    algo_name: str
    algo_params: Dict
    # Monitoring Data
    mon_params: List[str]


@router.get("/training/status/{model_id}", tags=["training"])
async def get_model_training_status(model_id: str):
    if not mongo.list_model(model_id):
        return {}

    return requests.get(f"http://detection_model_manager/training/{model_id}").json()


@router.post("/training/{app_name}", tags=["training"], deprecated=True)
async def start_training_model(
    app_name: str, body: ReqBody, reading_channel: Optional[str] = ""
):
    if body.ttime <= 0:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail="ttime needs to be strictly positive for training.",
        )

    resp = requests.get(f"http://detection_model_manager/algorithm/{body.algo_name}")
    if not resp or resp.status_code >= 400:
        raise HTTPException(resp.status_code, detail=resp.json().get("detail"))

    algo_details = resp.json()
    index_map_name = algo_details.get("index_map_name")
    user_filters = utils.select_data_filters(body.mon_params, body.docker_image)

    # Select data processing technique based on reps
    proc_technique = utils.define_processing_technique(algo_details, body.nreplicas)

    # Compute model_id for storing (metadata here | file on detection model manager)
    model = Model(
        body.app_name,
        body.algo_name,
        body.algo_params,
        proc_technique,
        body.service_name,
        body.docker_image,
        body.nreplicas,
    )

    if not mongo.insert_model(model):
        raise HTTPException(
            HTTPStatus.SERVICE_UNAVAILABLE, detail="Could not perform intended action."
        )

    proc_data = {
        "params": body.mon_params,
        "proc_technique": proc_technique,
        "reading_ch": app_name if not reading_channel else reading_channel,
        "user_filters": user_filters,
        "ttime": body.ttime,
        "index_map_name": index_map_name,
    }

    resp = requests.post(
        f"http://data_proc_agent/processing/data_processor", json=proc_data
    )
    if resp.status_code >= 400:
        return {}

    algo_data = {
        "det_model_id": model.get_id(),
        "params": body.algo_params,
        "name": body.algo_name,
        "ttime": body.ttime,
        "data_rch": resp.json().get("uid"),
    }
    resp = requests.post(f"http://detection_model_manager/training", json=algo_data)
    if resp.status_code >= 400:
        requests.delete(
            f"http://data_proc_agent/processing/data_processor/{algo_data['data_rch']}"
        )
        return {}

    feedback = resp.json() if resp.status_code < 400 else {}

    model_details = model.get_mongo_dict()
    model_details["_id"] = model.get_id()
    resp = requests.post(
        "http://metrics_engine/metrics/monitor/training",
        json={
            "model_details": model_details,
            "reading_ch": algo_data["data_rch"],
        },
    )
    if resp.status_code >= 400:
        requests.delete(f"http://detection_model_manager/training/{model.get_id()}")
        requests.delete(
            f"http://data_proc_agent/processing/data_processor/{algo_data['data_rch']}"
        )
        return {}

    return feedback


@router.delete("/training/{model_id}", tags=["training"])
async def abort_training_model(model_id: str):
    model = mongo.list_model(model_id)

    if model:
        mongo.delete_model(model_id)

    return requests.delete(f"http://detection_model_manager/training/{model_id}").json()
