from pydantic import BaseModel
from typing import List, Dict


class ServiceRelease(BaseModel):
    mri_cd_component: float = None
    version: str
    image_tag: str
    docker_image_sha: str
    active: bool = True


class Service(BaseModel):
    name: str
    docker_image_name: str
    algo_name: str
    algo_params: Dict
    passive_measure: bool = True
    versions: List[ServiceRelease] = []


class Application(BaseModel):
    app_name: str
    namespace: str
    monitor_filters: str
    services: List[Service] = []


class Cluster(BaseModel):
    hostname: str
    name: str
    api_token: str
    ca_file: str
    port: int = 443
    node_taints: List[str] = []
    applications: List[Application] = []
