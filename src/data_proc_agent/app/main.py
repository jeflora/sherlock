from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
import multiprocessing

from http import HTTPStatus
from typing import Dict

import app.data_processing.utils as utils
from app.data_processing import bridge


app = FastAPI(title="DATA PROCESSING AGENT")
jobs: Dict[str, utils.Job] = {}
procs: Dict[str, multiprocessing.Process] = {}


def start_processing_job(uid: str) -> None:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    (ric, roc, pc) = jobs[uid].get_configs()
    procs[uid] = multiprocessing.Process(
        target=bridge.process_data_traces, args=(ric, roc, pc, return_dict)
    )
    procs[uid].start()
    procs[uid].join()
    # jobs[uid].created_filename = return_dict.get(app_name)
    jobs[uid].done()


@app.get("/")
@app.get("/home")
async def root():
    return {"msg": "OK"}


@app.post(
    "/processing/data_processor", status_code=HTTPStatus.ACCEPTED, tags=["processing"]
)
async def init_data_processor(
    body: utils.JobRequestBody, background_tasks: BackgroundTasks, response: Response
):
    new_processing_job = utils.Job(body)

    if (
        new_processing_job.uid in jobs
        and jobs[new_processing_job.uid].status != "complete"
    ):
        response.status_code = HTTPStatus.OK
        return jobs[new_processing_job.uid]

    jobs[new_processing_job.uid] = new_processing_job
    background_tasks.add_task(start_processing_job, new_processing_job.uid)

    return new_processing_job


@app.delete(
    "/processing/data_processor/{uid}", status_code=HTTPStatus.OK, tags=["processing"]
)
async def stop_data_processor(uid: str):
    if uid not in jobs:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=f"Processing unit {uid} not found."
        )
    procs[uid].terminate()
    jobs[uid].status = "complete"
    return jobs[uid]


@app.get("/processing/status/{uid}", status_code=HTTPStatus.OK, tags=["processing"])
async def status_handler(uid: str):
    if uid not in jobs:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=f"Processing unit {uid} not found."
        )
    return jobs[uid]
