from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from typing_extensions import Annotated
import requests

import app.mongo.mongo_manager as mongo


router = APIRouter()


@router.get("/models", tags=["models"])
async def get_models(app_name: Optional[str] = ""):
    return mongo.list_models([{"app_name": app_name}] if app_name else [])


@router.get("/models/details", tags=["models"])
async def get_models_list_details(models: Annotated[List[str], Query()] = []):
    model_details = []
    for model_id in models:
        details = mongo.list_model(model_id)
        if not details:
            continue
        model_details.append(details)
    return model_details


@router.get("/model/{model_id}", tags=["models"])
async def get_model_details(model_id: str):
    return mongo.list_model(model_id)


@router.get("/models/{model_id}/metrics/mri/cd_component", tags=["models", "metrics"])
async def get_model_mri_cd_component(model_id: str):
    cd_value = mongo.get_model_cd_val(model_id)
    return {"cd": round(0.0 if cd_value == None else cd_value, 3)}


@router.delete("/model/{model_id}", tags=["models"])
async def delete_detection_model(model_id: str):
    model = mongo.list_model(model_id)
    if not model:
        raise HTTPException(
            HTTPStatus.NOT_FOUND, detail=f"Model with id {model_id} does not exist."
        )
    resp = requests.delete(f"http://detection_model_manager/model/{model_id}")
    if not resp or resp.status_code >= 400:
        raise HTTPException(resp.status_code, detail=resp.json().get("detail", ""))
    mongo.delete_model(model_id)
    return model
