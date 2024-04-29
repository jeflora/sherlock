from http import HTTPStatus
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import datetime, random

import app.cluster_info.config as clusters

router = APIRouter()


class MeasureReq(BaseModel):
    namespace: str


class MoveMeasureReq(MeasureReq):
    node_taints: List[str] = []


@router.post("/{cluster_name}/measures/restart/{service_name}", tags=["measures"])
async def restart_service_deployment(
    cluster_name: str, service_name: str, body: MeasureReq
):
    k8s_apps_api = clusters.get_appsv1_api_client(cluster_name)
    deployment = k8s_apps_api.read_namespaced_deployment(
        name=service_name, namespace=body.namespace
    )

    if not deployment:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Deployment not found.")

    deployment.spec.template.metadata.annotations = {
        "kubectl.kubernetes.io/restartedAt": datetime.datetime.now(
            datetime.UTC
        ).isoformat()
    }

    k8s_apps_api.patch_namespaced_deployment(
        body=deployment, name=service_name, namespace=body.namespace
    )

    return {"msg": "OK", "name": service_name}


@router.post("/{cluster_name}/measures/move/{service_name}", tags=["measures"])
async def move_service_deployment(
    cluster_name: str, service_name: str, body: MoveMeasureReq
):
    k8s_apps_api = clusters.get_appsv1_api_client(cluster_name)
    deployment = k8s_apps_api.read_namespaced_deployment(
        name=service_name, namespace=body.namespace
    )

    if not deployment:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Deployment not found.")

    cur_tolerations = deployment.spec.template.spec.tolerations
    if not cur_tolerations or not body.node_taints:
        return {"msg": "OK", "name": service_name}

    cur_tolerations_taints = list(map(lambda tnt: tnt.value, cur_tolerations))
    not_used_taints = [t for t in body.node_taints if t not in cur_tolerations_taints]
    if not not_used_taints:
        return {"msg": "OK", "name": service_name}

    taint_value = random.choice(not_used_taints)
    deployment.spec.template.spec.tolerations[0].value = taint_value

    k8s_apps_api.patch_namespaced_deployment(
        body=deployment, name=service_name, namespace=body.namespace
    )

    return {"msg": "OK", "name": service_name}
