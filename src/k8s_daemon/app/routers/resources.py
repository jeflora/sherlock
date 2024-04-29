from http import HTTPStatus
from fastapi import APIRouter, HTTPException

import app.cluster_info.config as clusters
import app.cluster_info.mongo as mongo

router = APIRouter()


# TODO: Reformulate API response messages
@router.get("/{cluster_name}/resources/{resource_type}", tags=["resources"])
async def get_resources(cluster_name: str, resource_type: str):
    k8s_core_api = clusters.get_corev1_api_client(cluster_name)
    if not k8s_core_api:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Cluster not found.")

    valid_resources = {
        "namespaces": k8s_core_api.list_namespace,
        "nodes": k8s_core_api.list_node,
    }

    if resource_type not in valid_resources:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Resource "{resource_type}" type not found. Resources available: {", ".join(valid_resources.keys())}',
        )

    response = valid_resources[resource_type](watch=False)
    names = []
    for resource in response.items:
        names.append(resource.metadata.name)
    return {"msg": "OK", "resource_type": resource_type, "resources": names}


@router.get("/{cluster_name}/resources/{namespace}/{resource_type}", tags=["resources"])
async def get_namespaced_resources(
    cluster_name: str, namespace: str, resource_type: str
):
    k8s_core_api = clusters.get_corev1_api_client(cluster_name)
    k8s_apps_api = clusters.get_appsv1_api_client(cluster_name)
    if not k8s_core_api or not k8s_apps_api:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Cluster not found.")

    valid_namespaces = await get_resources(cluster_name, "namespaces")
    valid_resources = {
        "daemonsets": k8s_apps_api.list_namespaced_daemon_set,
        "deployments": k8s_apps_api.list_namespaced_deployment,
        "services": k8s_core_api.list_namespaced_service,
        "pods": k8s_core_api.list_namespaced_pod,
    }

    if (
        namespace not in valid_namespaces.get("resources", [])
        or resource_type not in valid_resources
    ):
        # raise HTTPException(status_code=404, detail="Resource type not found.")
        return {
            "msg": "ERROR",
            "resource_type": resource_type,
            "namespace": namespace,
            "resources": [],
        }

    response = valid_resources[resource_type](namespace, watch=False)
    names = []
    for resource in response.items:
        names.append(resource.metadata.name)
    return {
        "msg": "OK",
        "resource_type": resource_type,
        "namespace": namespace,
        "resources": names,
    }


@router.get(
    "/{cluster_name}/resources/{namespace}/{service}/containers", tags=["resources"]
)
async def get_service_container_names(cluster_name: str, namespace: str, service: str):
    k8s_core_api = clusters.get_corev1_api_client(cluster_name)
    if not k8s_core_api:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Cluster not found.")

    valid_namespaces = await get_resources(cluster_name, "namespaces")
    valid_services = await get_namespaced_resources(cluster_name, namespace, "services")

    if namespace not in valid_namespaces.get(
        "resources", []
    ) or service not in valid_services.get("resources", []):
        # raise HTTPException(status_code=404, detail="Resource type not found.")
        return {
            "msg": "ERROR",
            "namespace": namespace,
            "service": service,
            "containers": [],
        }

    selector = ""
    services = k8s_core_api.list_namespaced_service(namespace, watch=False).items
    for srv in services:
        if srv.metadata.name == service:
            selector = f"run={srv.spec.selector['run']}"

    if not selector:
        # raise HTTPException(status_code=404, detail="Resource type not found.")
        return {
            "msg": "ERROR",
            "namespace": namespace,
            "service": service,
            "containers": [],
        }

    containers = []
    pods_list = k8s_core_api.list_namespaced_pod(
        namespace, label_selector=selector, watch=False
    )
    for pod in pods_list.items:
        containers.append(
            {
                "id": pod.status.container_statuses[0].container_id,
                "image_id": pod.status.container_statuses[0].image_id,
                "node": pod.spec.node_name,
            }
        )

    return {
        "msg": "OK",
        "namespace": namespace,
        "service": service,
        "containers": containers,
    }
