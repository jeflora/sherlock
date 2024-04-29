from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from http import HTTPStatus
from typing import Dict
import os

import app.detection.detector as dm


router = APIRouter()


detection_models: Dict[str, dm.DetectionModel] = {}


def run_detection_model(model_id: str):
    detection_models[model_id].mstatus = dm.ModelStatus.RUNNING
    detection_models[model_id].start()
    detection_models[model_id].join()
    detection_models[model_id].mstatus = dm.ModelStatus.COMPLETE


@router.get("/detection/models/running", tags=["detection"])
async def get_detection_models_running():
    models = []
    for model_id in detection_models:
        if detection_models[model_id].mstatus == dm.ModelStatus.RUNNING:
            models.append(model_id)
    return models


@router.get("/detection/{model_id}", tags=["detection"])
async def get_status_model_detection(model_id: str):
    if model_id not in detection_models:
        return {}

    return detection_models[model_id].get_data()


@router.post(
    "/detection/{model_id}", tags=["detection"], status_code=HTTPStatus.ACCEPTED
)
async def start_detection_model(
    model_id: str, request: Request, background_tasks: BackgroundTasks
):
    req_params = ["data_rch", "app_name", "service_name"]
    if not await request.body():
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Request body missing {','.join(req_params)} parameters.",
        )

    data = await request.json()
    if not all(p in data for p in req_params):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Request body missing {','.join(req_params)} parameters.",
        )

    if (
        model_id in detection_models
        and detection_models[model_id].mstatus != dm.ModelStatus.COMPLETE
    ):
        return detection_models[model_id].get_data()

    if not os.path.isfile(os.path.join(os.getenv("MODEL_PATH_DIR"), model_id)):
        raise HTTPException(
            HTTPStatus.NOT_FOUND, detail=f"Model {model_id} file not found."
        )

    detection_models[model_id] = dm.DetectionModel(
        model_id, data.get("data_rch"), data.get("app_name"), data.get("service_name")
    )
    background_tasks.add_task(run_detection_model, model_id)

    return detection_models[model_id].get_data()


@router.delete("/detection/{model_id}", tags=["detection"])
async def stop_detection_model(model_id: str):
    if model_id not in detection_models:
        return {}

    if detection_models[model_id].mstatus == dm.ModelStatus.RUNNING:
        detection_models[model_id].stop_detection()
        detection_models[model_id].mstatus == dm.ModelStatus.COMPLETE

    return detection_models[model_id].get_data()
