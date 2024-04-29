from ast import mod
from typing import Dict, Optional
from fastapi import BackgroundTasks, FastAPI, Request, HTTPException
from http import HTTPStatus

import app.metrics.utils as mon
import app.metrics.mri as mri

app = FastAPI(title="METRICS ENGINE")


monitors: Dict[str, mon.Monitor] = {}


def run_monitor(model_id: str):
    monitors[model_id].mstatus = mon.MonitorStatus.RUNNING
    monitors[model_id].start()
    monitors[model_id].join()
    monitors[model_id].mstatus = mon.MonitorStatus.COMPLETE


@app.get("/")
@app.get("/home")
async def root():
    return {"msg": "OK"}


@app.get("/metrics/mri/{model_id}", tags=["metrics"])
async def get_mri_computation(model_id: str, last_minutes: Optional[int] = 10):
    return {"mri": {"value": round(mri.compute_metric(model_id, last_minutes), 3)}}


@app.post("/metrics/monitor/{operation_mode}", tags=["metrics"])
async def monitor_data_stream(
    operation_mode: str, request: Request, background_tasks: BackgroundTasks
):

    if operation_mode not in ["training", "detection"]:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Operation mode should be either training or detection.",
        )

    req_params = ["model_details", "reading_ch"]
    if not await request.body():
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Request body missing {','.join(req_params)} parameters.",
        )

    data = await request.json()
    if not all(par in data for par in req_params):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Request body missing {','.join(req_params)} parameters.",
        )
    model_id = data.get("model_details").get("_id")

    if (
        model_id in monitors
        and monitors[model_id].mstatus != mon.MonitorStatus.COMPLETE
        and monitors[model_id].op_mode == operation_mode
    ):
        return monitors[model_id].get_data()

    monitors[model_id] = mon.Monitor(
        operation_mode, model_id, data.get("model_details"), data.get("reading_ch")
    )
    background_tasks.add_task(run_monitor, model_id)

    return monitors[model_id].get_data()


@app.delete("/metrics/monitor/{model_id}", tags=["metrics"])
async def stop_monitor_data_stream(model_id: str):
    if model_id not in monitors:
        return {}

    if monitors[model_id].mstatus != mon.MonitorStatus.COMPLETE:
        monitors[model_id].stop_monitor()
        monitors[model_id].mstatus = mon.MonitorStatus.COMPLETE

    return monitors[model_id].get_data()
