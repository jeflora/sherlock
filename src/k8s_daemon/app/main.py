from http import HTTPStatus
from fastapi import FastAPI, HTTPException, Request
import requests
from bson.objectid import ObjectId
from typing import Optional
import os, hashlib
from app.routers import resources, monitoring, measures
import app.cluster_info.mongo as mongo

app = FastAPI(title="K8S DAEMON")
app.include_router(resources.router)
app.include_router(monitoring.router)
app.include_router(measures.router)


@app.get("/")
@app.get("/home")
async def root():
    return {"msg": "OK"}


@app.delete("/reset")
async def delete():
    """For Script Testing Purposes"""
    mongo.get_clusters_collection().delete_many({})
    return {"msg": "OK"}


@app.get("/clusters", tags=["clusters"])
async def get_cluster(cluster_name: Optional[str] = None):
    return (
        mongo.get_cluster_data(cluster_name) if cluster_name else mongo.get_clusters()
    )


@app.post("/cluster", tags=["cluster"], status_code=HTTPStatus.CREATED)
async def store_cluster_details(request: Request):
    cluster_data = await request.json()

    app_data = cluster_data.pop("applications", [])

    if not cluster_data["ca_file"] in await get_certificates():
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            detail=f"File {cluster_data['ca_file']} not found. Upload first using /cluster/upload.",
        )

    hash = hashlib.shake_256()
    hash.update(bytes(cluster_data.get("hostname"), encoding="utf-8"))
    id_hash = hash.hexdigest(12)
    obj_id = ObjectId(id_hash)

    cluster_data["_id"] = obj_id
    if not mongo.insert_cluster_data(cluster_data):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST, detail=f"This cluster already exists."
        )

    cluster_data["_id"] = id_hash
    cluster_data["applications"] = app_data
    resp = requests.post(
        f"http://management_engine/automation/clusters", json=cluster_data
    )
    if resp.status_code >= 400:
        mongo.delete_cluster_data(cluster_data["name"])
        raise HTTPException(
            HTTPStatus.SERVICE_UNAVAILABLE, detail=f"Could not statisfy request."
        )

    return {"id": id_hash}


@app.get("/cluster/certificates", tags=["cluster"])
async def get_certificates():
    return [f for f in os.listdir("/crt_files") if f.endswith(".crt")]


@app.post("/cluster/upload", tags=["cluster"], status_code=HTTPStatus.CREATED)
async def upload_ca_file(request: Request):
    req_params = ["filename", "ca_contents"]
    body = await request.json()
    if not all(par in body for par in req_params):
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Missing certificate data.")

    contents = "\n".join(body["ca_contents"])
    with open(f"/crt_files/{body['filename']}", "w") as fp:
        fp.write(contents)

    return {"msg": "OK"}
