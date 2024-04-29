from http import HTTPStatus
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from typing import Optional, List

from app.daemon.daemonclient import DaemonClient
from app.automation import models
import os


router = APIRouter()


class ReqBody(BaseModel):
    name: str
    hostname: str
    port: int = 443
    api_token: str
    filename: str


daemon_client = DaemonClient(os.getenv("DAEMON_HOST"), os.getenv("DAEMON_PORT"))


@router.get("/cluster/namespaces/resources/", tags=["cluster"])
async def get_available_namespaces_resources(type: Optional[str] = None):
    available = ["daemonsets", "deployments", "services", "pods"]
    return [] if type and type not in available else available


@router.get("/cluster/{cluster_name}/{resource}/", tags=["cluster"])
async def get_resources(cluster_name: str, resource: str, name: Optional[str] = None):
    items = daemon_client.get_resources_list(cluster_name, resource).get(
        "resources", []
    )
    return [] if name and name not in items else [{"name": item} for item in items]


@router.get("/cluster/{cluster_name}/{namespace}/{resource}/", tags=["cluster"])
async def get_resources(cluster_name: str, namespace: str, resource: str):
    available = ["daemonsets", "deployments", "services", "pods"]
    if resource not in available:
        return []
    items = daemon_client.get_namespaced_resources_list(
        cluster_name, namespace, resource
    ).get("resources", [])
    return [{"name": item} for item in items]


@router.get("/clusters", tags=["cluster"])
async def get_cluster(cluster_name: Optional[str] = None):
    return daemon_client.get_cluster_info(cluster_name)


@router.get("/clusters/names", tags=["cluster"])
async def get_cluster_names():
    return list(map(lambda x: x.get('name'), (await get_cluster())))


@router.post("/cluster", tags=["cluster"])
async def create_cluster(new_cluster: models.Cluster):
    return {"msg": "OK"} if daemon_client.create_cluster(new_cluster.model_dump()) else {}


@router.get("/cluster/certificates", tags=["cluster"])
async def list_certificate_files():
    return daemon_client.get_certificate_files()


@router.post("/cluster/upload/certificate", tags=["cluster"])
async def upload_certificate_file(ca_file: UploadFile):
    contents = (await ca_file.read()).decode("utf-8").split("\n")
    filename = ca_file.filename
    return (
        {"msg": "OK"}
        if daemon_client.upload_ca_file({"ca_contents": contents, "filename": filename})
        else {}
    )
