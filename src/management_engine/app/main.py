from fastapi import FastAPI
from app.routers import models, training, detection, automation, measures

import app.mongo.mongo_manager as mongo

app = FastAPI(title="MGMT ENGINE")
app.include_router(models.router)
app.include_router(training.router)
app.include_router(detection.router)
app.include_router(automation.router)
app.include_router(measures.router)


@app.get("/", tags=["home"])
@app.get("/home", tags=["home"])
async def root():
    return {"msg": "OK"}


@app.delete("/reset", tags=["home"])
async def delete():
    """ For Script Testing Purposes"""
    mongo.get_models_meta_collection().delete_many({})
    mongo.get_clusters_collection().delete_many({})
    return {"msg": "OK"}