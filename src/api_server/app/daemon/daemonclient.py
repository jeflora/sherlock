import json
import requests


class DaemonClient:
    def __init__(self, daemon_ip, daemon_port):
        self.host = f"http://{daemon_ip}:{daemon_port}"

    def _get(self, endpoint):
        resp = requests.get(f"{self.host}/{endpoint}")
        return resp.json() if resp.status_code < 400 else {}

    def _post(self, endpoint, params=None):
        resp = requests.post(f"{self.host}/{endpoint}", json=params)
        return resp.json() if resp.status_code < 400 else {}

    def _delete(self, endpoint):
        resp = requests.delete(f"{self.host}/{endpoint}")
        return resp.json() if resp.status_code < 400 else {}

    def _put(self):
        pass

    def get_resources_list(self, cluster_name: str, resource_type: str):
        return self._get(f"{cluster_name}/resources/{resource_type}")

    def get_namespaced_resources_list(
        self, cluster_name, namespace, resource_type: str
    ):
        return self._get(f"{cluster_name}/resources/{namespace}/{resource_type}")

    def start_data_collection(
        self,
        cluster_name: str,
        app_name: str,
        namespace: str,
        monitor_filters: list,
        node_taints: list,
    ):
        return self._post(
            f"{cluster_name}/monitoring/start/{namespace}/{app_name}",
            params={"monitoring_params": monitor_filters, "node_taints": node_taints},
        )

    def close_data_collection(self, cluster_name: str, app_name: str, namespace: str):
        return self._delete(f"{cluster_name}/monitoring/stop/{namespace}/{app_name}")

    def get_monitoring_params(self):
        return self._get("monitoring/params")

    def get_service_nreplicas(self, service_name: str):
        # TODO: Implement this correctly...
        return 1

    def get_service_docker_image(self, service_name: str):
        # TODO: Implement this correctly...
        return "flora/teastore-webui"

    def get_cluster_info(self, name):
        resp = self._get(f"clusters{'' if not name else f'?cluster_name={name}'}")
        if not resp:
            return [] if not name else resp

        for cl in resp if not name else [resp]:
            cl.pop("api_token", None)
            cl.pop("filename", None)
            cl.pop("ca_filepath", None)

        return resp

    def create_cluster(self, data: dict):
        return self._post("cluster", params=data)

    def get_certificate_files(self):
        files = self._get("cluster/certificates")
        return [] if not files else files

    def upload_ca_file(self, contents):
        return self._post("cluster/upload", params=contents)
