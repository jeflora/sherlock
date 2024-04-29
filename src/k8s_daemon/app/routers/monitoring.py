from http import HTTPStatus
from fastapi import APIRouter, Request, HTTPException, Response
from pydantic import BaseModel
from typing import List
import re, asyncio

from kubernetes.client.rest import ApiException

from app.routers import utils, resources
import app.cluster_info.config as clusters

router = APIRouter()


sysdig_params = [
    "%evt.rawtime",
    "%container.name",
    "%container.image.repository",
    "%thread.tid",
    "%evt.dir",
    "%evt.category",
    "%syscall.type",
    "%evt.args",
]
# sysdig_filters = ["container.name contains k8s_teastore"]

DAEMONSET_ID = "daemonset-sysdig-{cluster_name}-{namespace}"


class Container(BaseModel):
    id: str
    image_id: str
    node: str


class Monitor(BaseModel):
    service_name: str
    parameters: str
    containers: List[Container]


monitoring_units = {}


@router.get("/monitoring/params", tags=["monitoring"], status_code=200)
async def get_monitoring_params():
    return [param.replace("%", "").replace(".", "_") for param in sysdig_params]


class MonUnitReq(BaseModel):
    node_taints: List[str] = []


class ClustMonReq(MonUnitReq):
    monitoring_params: List[str] = []


@router.post(
    "/{cluster_name}/monitoring/start/{namespace}/{app}",
    tags=["monitoring"],
    status_code=HTTPStatus.OK,
)
async def start_monitoring_unit(
    cluster_name: str, namespace: str, app: str, body: ClustMonReq, response: Response
):
    sysdig_filters = body.monitoring_params

    daemonset = await create_monitoring_unit(cluster_name, namespace, body, response)
    daemonset_id = daemonset.get("id", None)

    if not daemonset_id:
        raise HTTPException(
            HTTPStatus.NOT_FOUND, detail="Monitoring unit not found. Create unit first."
        )

    k8s_core_api = clusters.get_corev1_api_client(cluster_name)
    if not k8s_core_api:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Cluster not found.")

    daemonset_pods_list = k8s_core_api.list_namespaced_pod(
        namespace, label_selector=f"name={daemonset_id}", watch=False
    )

    if not daemonset_pods_list:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Daemonset not found.")
    names = [pod.metadata.name for pod in daemonset_pods_list.items]

    for pod_name in names:
        dicto_key = f"{cluster_name}-{namespace}-{app}-{pod_name}"

        if dicto_key not in monitoring_units:
            monitoring_units[dicto_key] = utils.SysdigMonitor(
                cluster_name, app, pod_name
            )
            monitoring_units[dicto_key].start_monitoring(
                namespace, sysdig_params, sysdig_filters
            )
        else:  # update
            monitoring_units[dicto_key].update_monitoring(
                namespace, sysdig_params, sysdig_filters
            )

    return {"msg": "OK"}


@router.delete("/{cluster_name}/monitoring/stop/{namespace}/{app}", tags=["monitoring"])
def stop_monitoring_unit(cluster_name: str, namespace: str, app: str):
    del_keys = []
    for dicto_key in monitoring_units:
        if all(pr in dicto_key for pr in [cluster_name, namespace, app]):
            monitoring_units[dicto_key].stop_monitoring()
            del_keys.append(dicto_key)

    for dicto_key in del_keys:
        if dicto_key in monitoring_units:
            del monitoring_units[dicto_key]

    return {"msg": "OK"}


def get_daemonset_id(cluster_name: str, namespace: str):
    daemonset_id = DAEMONSET_ID.format(cluster_name=cluster_name, namespace=namespace)
    return re.sub("[^0-9a-zA-Z]+", "-", daemonset_id)


@router.post(
    "/{cluster_name}/monitoring/{namespace}/",
    tags=["monitoring"],
    status_code=HTTPStatus.OK,
)
async def create_monitoring_unit(
    cluster_name: str, namespace: str, body: MonUnitReq, response: Response
):
    """
    Create monitoring unit
    """

    valid_namespaces = await resources.get_resources(cluster_name, "namespaces")
    if namespace not in valid_namespaces.get("resources", []):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Namespace not found."
        )

    daemonset_id = get_daemonset_id(cluster_name, namespace)
    daemonsets = await resources.get_namespaced_resources(
        cluster_name, namespace, "daemonsets"
    )

    k8s_apps_api = clusters.get_appsv1_api_client(cluster_name)
    if not k8s_apps_api:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Cluster not found.")

    if daemonset_id not in daemonsets.get("resources", []):
        # Create the Daemonset
        daemon_set_object = utils.create_monitoring_daemon_set_object(
            daemonset_id, nodes_taints=body.node_taints
        )
        resp = k8s_apps_api.create_namespaced_daemon_set(
            namespace=namespace, body=daemon_set_object
        )
        response.status_code = HTTPStatus.CREATED
        await asyncio.sleep(2)

    return {"msg": "OK", "id": daemonset_id}


@router.delete(
    "/{cluster_name}/monitoring/{namespace}",
    tags=["monitoring"],
    status_code=HTTPStatus.OK,
)
def delete_monitoring_unit(cluster_name: str, namespace: str):
    """
    Delete running monitoring unit with id
    """
    k8s_apps_api = clusters.get_appsv1_api_client(cluster_name)
    if not k8s_apps_api:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Cluster not found.")

    del_keys = []
    for dicto_key in monitoring_units:
        if all(pr in dicto_key for pr in [cluster_name, namespace]):
            monitoring_units[dicto_key].stop_monitoring()
            del_keys.append(dicto_key)

    for dicto_key in del_keys:
        monitoring_units.pop(dicto_key, None)

    try:
        daemonset_id = get_daemonset_id(cluster_name, namespace)
        k8s_apps_api.delete_namespaced_daemon_set(
            name=daemonset_id, namespace=namespace
        )
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=f"Error: {e}")

    return {"msg": "OK", "id": daemonset_id}
