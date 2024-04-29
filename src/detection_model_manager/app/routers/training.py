from http import HTTPStatus
from fastapi import BackgroundTasks, APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import multiprocessing, os

import app.training.train_model as train
import app.algorithms.metadata as meta


router = APIRouter()


class ReqModelBody(BaseModel):
    name: str
    params: Dict
    det_model_id: str
    data_rch: str
    ttime: int
    status: str = "in_progress"


model_training: Dict[str, ReqModelBody] = {}
procs: Dict[str, multiprocessing.Process] = {}


def start_training_model(model_id: str) -> None:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    algo_name, algo_params, reading_ch = (
        model_training[model_id].name,
        model_training[model_id].params,
        model_training[model_id].data_rch,
    )
    procs[model_id] = multiprocessing.Process(
        target=train.train_detection_model,
        args=(model_id, algo_name, algo_params, reading_ch, return_dict),
    )
    procs[model_id].start()
    procs[model_id].join()
    model_training[model_id].status = "complete"


@router.get("/training/{model_id}", tags=["training"])
async def get_status_model_training(model_id: str):
    if not model_id in model_training:
        return {}

    return model_training[model_id]


@router.post("/training", tags=["training"], status_code=HTTPStatus.ACCEPTED)
async def train_model(body: ReqModelBody, background_tasks: BackgroundTasks):
    if not meta.check_params_for_algorithm(body.name, body.params):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail="Configuration of the algorithm does not fit requirements. Check /algorithms or /algorithm/\{algo_name\}.",
        )

    model_training[body.det_model_id] = body
    background_tasks.add_task(start_training_model, body.det_model_id)

    return model_training[body.det_model_id]


@router.delete("/training/{model_id}", tags=["training"])
async def stop_model_training(model_id: str):
    if not model_id in model_training:
        return {}

    if model_training[model_id].status == "in_progress":
        procs[model_id].terminate()
        model_training[model_id].status = "complete"

    return model_training[model_id]


@router.delete("/model/{model_id}", tags=["models"], status_code=HTTPStatus.OK)
async def delete_detection_model(model_id: str):
    filepath = os.path.join(os.getenv("MODEL_PATH_DIR"), model_id)
    if not os.path.isfile(filepath):
        raise HTTPException(HTTPStatus.NOT_FOUND, detail=f"Model {model_id} not found.")
    os.remove(filepath)
    return {"msg": "OK"}
