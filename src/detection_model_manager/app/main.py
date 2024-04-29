from fastapi import FastAPI, HTTPException
from http import HTTPStatus

import app.algorithms.metadata as meta
from app.routers import alarms, training, detection


app = FastAPI(title="DETECTION MODEL MANAGER")
app.include_router(training.router)
app.include_router(detection.router)
app.include_router(alarms.router)


@app.get("/")
@app.get("/home")
async def root():
    return {"msg": "OK"}


@app.get("/algorithms", tags=["algorithms"])
async def get_algorithms_available():
    return meta.ALGOS_AVAILABLE


@app.get("/algorithm/{algo_name}", tags=["algorithms"])
async def get_algorithm_details(algo_name: str):
    if algo_name not in meta.ALGOS_AVAILABLE.keys():
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            detail=f"{algo_name} algorithm not found. Algos available: {','.join(meta.ALGOS_AVAILABLE.keys())}",
        )
    return meta.ALGOS_AVAILABLE.get(algo_name)
