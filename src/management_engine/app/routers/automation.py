from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import requests
from bson.objectid import ObjectId


import app.mongo.mongo_manager as mongo
from app.automation import models
import app.routers.training as train

router = APIRouter()


MIN_SECONDS = 60


@router.get("/cluster/{app_name}", tags=["clusters"])
async def get_cluster_with_app_name(app_name: str):
    return {"name": mongo.get_cluster_name_from_app_name(app_name)}


async def init_monitoring_unit(cluster_name: str, app_details: dict):
    cluster_details = mongo.get_cluster_from_name(cluster_name)
    # Deploy a monitoring unit...
    resp = requests.post(
        f"http://k8s_daemon/{cluster_name}/monitoring/{app_details['namespace']}/",
        json={'node_taints': cluster_details.get('node_taints', [])}
    )

    return resp.status_code in [HTTPStatus.OK, HTTPStatus.CREATED]


@router.post(
    "/automation/clusters/",
    tags=["automation", "clusters"],
    status_code=HTTPStatus.CREATED,
)
async def create_cluster(request: Request):
    cluster_data = await request.json()
    id = cluster_data["_id"]

    cluster_data["_id"] = ObjectId(id)
    if not mongo.insert_cluster(cluster_data):
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Error creating cluster.")

    for app in cluster_data.get('applications', []):
        await init_monitoring_unit(cluster_data["name"], app)

    return {"id": id, "name": cluster_data["name"]}


@router.get("/cluster/{cluster_name}/app_names", tags=["clusters"])
@router.get("/automation/{cluster_name}/list/apps", tags=["automation", "apps"])
async def get_cluster_apps(cluster_name: str):
    return mongo.get_cluster_app_names(cluster_name)


@router.get("/cluster/app_details/{app_name}", tags=["automation", "apps"])
async def list_app_details_from_name(app_name: str):
    return mongo.list_app_details(
        mongo.get_cluster_name_from_app_name(app_name), app_name
    )


@router.get("/automation/{cluster_name}/{app_name}", tags=["automation", "apps"])
async def list_app_details(cluster_name: str, app_name: str):
    return mongo.list_app_details(cluster_name, app_name)


@router.post("/automation/{cluster_name}/add/application", tags=["automation", "apps"])
async def add_app_to_cluster(cluster_name: str, app_to_add: models.Application):
    new_app = app_to_add.model_dump()

    if not mongo.add_app_to_cluster(cluster_name, new_app):
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    return {
        "app_name": new_app.get("app_name"),
        "monitoring_unit": "OK" if (await init_monitoring_unit(cluster_name, new_app)) else "ERROR",
    }


@router.delete("/automation/{cluster_name}/{app_name}", tags=["automation", "apps"])
async def delete_app_from_cluster(cluster_name: str, app_name: str):
    if not mongo.delete_app_from_cluster(cluster_name, app_name):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return {"app_name": app_name}


@router.get(
    "/automation/{cluster_name}/{app_name}/list/services", tags=["automation", "apps"]
)
async def list_service_details(cluster_name: str, app_name: str):
    return mongo.list_app_services(cluster_name, app_name)


@router.post(
    "/automation/{cluster_name}/{app_name}/add/service", tags=["automation", "services"]
)
async def add_service_to_app(
    cluster_name: str, app_name: str, service_to_add: models.Service
):
    new_service = service_to_add.model_dump()
    if not mongo.add_service_to_app(cluster_name, app_name, new_service):
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    return {"name": new_service.get("name")}


@router.delete(
    "/automation/{cluster_name}/{app_name}/{service_name}",
    tags=["automation", "services"],
)
async def delete_service_from_app(cluster_name: str, app_name: str, service_name: str):
    if not mongo.delete_service_from_app(cluster_name, app_name, service_name):
        raise HTTPException(HTTPStatus.NOT_FOUND)

    return {"name": service_name}


@router.get(
    "/automation/{cluster_name}/{app_name}/{service_name}/list/releases",
    tags=["automation", "service_releases"],
)
async def list_service_releases(cluster_name: str, app_name: str, service_name: str):
    return mongo.list_service_releases(cluster_name, app_name, service_name)


@router.post(
    "/automation/{cluster_name}/{app_name}/{service_name}/add/release",
    tags=["automation", "service_releases"],
)
async def add_release_to_service(
    cluster_name: str,
    app_name: str,
    service_name: str,
    release_to_add: models.ServiceRelease,
):

    new_release = release_to_add.model_dump()
    if (
        mongo.list_service_releases(cluster_name, app_name, service_name)
        and new_release.get("mri_cd_component", None) == None
    ):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Service {service_name} has past releases. CD component needs to be provided.",
        )

    if not mongo.add_release_to_service(
        cluster_name, app_name, service_name, new_release
    ):
        raise HTTPException(HTTPStatus.BAD_REQUEST)

    return {"service": service_name, "name": new_release.get("version")}


class TrainModel(BaseModel):
    staging: bool = False
    reading_ch: str = ""
    ttime: int = 10  # minutes
    nreplicas: int = 1


@router.post(
    "/automation/training/{app_name}/{service_name}", tags=["training", "automation"]
)
async def start_training_model(
    app_name: str,
    service_name: str,
    body: TrainModel,
):
    resp = requests.get("http://k8s_daemon/monitoring/params")
    if resp.status_code >= 400:
        raise HTTPException(HTTPStatus.SERVICE_UNAVAILABLE)

    reading_ch = (
        app_name
        if not body.staging
        else (f"staging-{app_name}" if not body.reading_ch else body.reading_ch)
    )

    if not body.staging:
        # FIXME: Preciso de obter dados do K8S daemon
        nreplicas = 1

    mon_params = resp.json()
    db_data = mongo.get_service_monitoring_data(app_name, service_name)

    model = train.ReqBody(
        app_name=app_name,
        ttime=body.ttime * MIN_SECONDS,  # seconds
        service_name=service_name,
        nreplicas=nreplicas,
        docker_image=db_data.get("docker_image_name"),
        algo_name=db_data.get("algo_name"),
        algo_params=db_data.get("algo_params"),
        mon_params=mon_params,
    )

    return await train.start_training_model(app_name, model, reading_ch)
