from fastapi import APIRouter
import requests

from app.automation import models


router = APIRouter()


@router.get("/automation/{cluster_name}/list/apps", tags=["automation", "apps"])
async def list_apps_in_cluster(cluster_name: str):
    resp = requests.get(f"http://management_engine/automation/{cluster_name}/list/apps")
    return resp.json() if resp.status_code < 400 else []


@router.get("/automation/{cluster_name}/list/apps/names", tags=["automation", "apps"])
async def list_apps_names(cluster_name: str):
    return await list_apps_in_cluster(cluster_name)


@router.get("/automation/{cluster_name}/{app_name}", tags=["automation", "apps"])
async def list_app_details(cluster_name: str, app_name: str):
    resp = requests.get(
        f"http://management_engine/automation/{cluster_name}/{app_name}"
    )
    return resp.json() if resp.status_code < 400 else {}


@router.post("/automation/{cluster_name}/add/application", tags=["automation", "apps"])
async def add_app_to_cluster(cluster_name: str, app_to_add: models.Application):
    resp = requests.post(
        f"http://management_engine/automation/{cluster_name}/add/application",
        json=app_to_add.model_dump(),
    )
    return resp.json() if resp.status_code < 400 else {}


@router.delete("/automation/{cluster_name}/{app_name}", tags=["automation", "apps"])
async def delete_app_from_cluster(cluster_name: str, app_name: str):
    resp = requests.delete(
        f"http://management_engine/automation/{cluster_name}/{app_name}"
    )
    return resp.json() if resp.status_code < 400 else {}


@router.get(
    "/automation/{cluster_name}/{app_name}/list/services",
    tags=["automation", "services"],
)
async def list_app_services(cluster_name: str, app_name: str):
    resp = requests.get(
        f"http://management_engine/automation/{cluster_name}/{app_name}/list/services"
    )
    return resp.json() if resp.status_code < 400 else []


@router.get(
    "/automation/{cluster_name}/{app_name}/list/services/names",
    tags=["automation", "services"],
)
async def list_app_services_names(cluster_name: str, app_name: str):
    return list(
        map(lambda x: x.get("name"), (await list_app_services(cluster_name, app_name)))
    )


@router.post(
    "/automation/{cluster_name}/{app_name}/add/service", tags=["automation", "services"]
)
async def add_service_to_app(
    cluster_name: str, app_name: str, service_to_add: models.Service
):
    resp = requests.post(
        f"http://management_engine/automation/{cluster_name}/{app_name}/add/service",
        json=service_to_add.model_dump(),
    )
    return resp.json() if resp.status_code < 400 else {}


@router.delete(
    "/automation/{cluster_name}/{app_name}/{service_name}",
    tags=["automation", "services"],
)
async def delete_service_from_app(cluster_name: str, app_name: str, service_name: str):
    resp = requests.delete(
        f"http://management_engine/automation/{cluster_name}/{app_name}/{service_name}"
    )
    return resp.json() if resp.status_code < 400 else {}


@router.get(
    "/automation/{cluster_name}/{app_name}/{service_name}/list/releases",
    tags=["automation", "service_releases"],
)
async def list_service_releases(cluster_name: str, app_name: str, service_name: str):
    resp = requests.get(
        f"http://management_engine/automation/{cluster_name}/{app_name}/{service_name}/list/releases"
    )
    return resp.json() if resp.status_code < 400 else []


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
    data = release_to_add.model_dump()
    if release_to_add.mri_cd_component == None:
        data.pop("mri_cd_component", None)
    resp = requests.post(
        f"http://management_engine/automation/{cluster_name}/{app_name}/{service_name}/add/release",
        json=data,
    )
    return resp.json() if resp.status_code < 400 else {}
