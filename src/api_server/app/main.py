from fastapi import FastAPI
from app.routers import (
    cluster,
    monitoring,
    traces,
    intrusion_detection,
    alarms,
    automation,
)
import requests
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="API SERVER")
app.include_router(cluster.router)
app.include_router(monitoring.router)
app.include_router(traces.router)
app.include_router(intrusion_detection.router)
app.include_router(alarms.router)
app.include_router(automation.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/home")
async def root():
    return {"msg": "OK"}


@app.delete("/reset")
async def testing_reset():
    """For Script Testing Purposes"""
    requests.delete("http://k8s_daemon/reset")
    requests.delete("http://management_engine/reset")
    return {"msg": "OK"}
