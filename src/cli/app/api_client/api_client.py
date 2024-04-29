import requests, pprint


class APIClient:
    def __init__(self, api_url):
        self.host = api_url

    def _get(self, endpoint, params={}):
        resp = requests.get(f"{self.host}/{endpoint}", params=params)
        return resp.json() if resp.status_code < 400 else {}

    def _post(self, endpoint, data):
        resp = requests.post(f"{self.host}/{endpoint}", json=data)
        return resp.json() if resp.status_code < 400 else {}

    def _put(self):
        pass

    def _delete(self, endpoint):
        resp = requests.delete(f"{self.host}/{endpoint}")
        return resp.json() if resp.status_code < 400 else {}

    def get_resources_list(self, cluster_name: str, resource_type: str):
        pprint.pprint(self._get(f"cluster/{cluster_name}/{resource_type}"))

    def get_namespaced_resources_list(
        self, cluster_name: str, namespace: str, resource_type: str
    ):
        pprint.pprint(self._get(f"cluster/{cluster_name}/{namespace}/{resource_type}"))

    def get_certificates_files(self):
        return self._get("cluster/certificates")

    def get_cluster_resources(
        self,
        name: str,
        cluster_name: str,
        namespace: str,
        app_name: str,
        service_name: str,
    ):
        resources, error = None, None
        if name == "certificates":
            resources = self.get_certificates_files()
        elif name == "cluster":
            resources = self._get(
                "clusters", {} if not cluster_name else {"cluster_name": cluster_name}
            )
        elif name == "application":
            if not cluster_name:
                error = "cluster name not found"
            else:
                resources = self._get(
                    f"automation/{cluster_name}/list/apps"
                    if not app_name
                    else f"automation/{cluster_name}/{app_name}"
                )
        elif name == "service":
            print(cluster_name, app_name)
            if not cluster_name or not app_name:
                error = "cluster name or app-name not found"
            else:
                resources = self._get(
                    f"automation/{cluster_name}/{app_name}/list/services"
                )
        elif name == "release":
            if not cluster_name or not app_name or not service_name:
                error = "cluster name, app-name or service_name not found"
            else:
                resources = self._get(
                    f"automation/{cluster_name}/{app_name}/{service_name}/list/releases"
                )
        elif name == "monitoring":
            if not cluster_name or not app_name:
                error = "cluster name or app-name not found"
            else:
                resources = self._get(f"monitoring/status/{app_name}")
        elif name == "models":
            if not cluster_name or not app_name:
                error = "cluster name or app-name not found"
            else:
                resources = self._get("intrusion/models", params={"app_name": app_name})
        elif name == "traces":
            if not cluster_name:
                error = "cluster name not found"
            else:
                resources = self._get("traces")

        if error is not None:
            print(error)
        elif not resources:
            print("No resources found.")
        else:
            pprint.pprint(resources)

        return

    def create_cluster(self, data):
        result = (
            "cluster created"
            if self._post("cluster", data).get("msg") == "OK"
            else "error! cluster not created"
        )
        print(result)

    def create_application(self, data):
        cluster_name = data.pop("cluster_name", None)
        result = "error! cluster_name not found"
        if cluster_name:
            result = (
                "application created"
                if self._post(f"automation/{cluster_name}/add/application", data).get(
                    "app_name"
                )
                == data["app_name"]
                else "error! application not created"
            )
        print(result)

    def create_service(self, data):
        cluster_name = data.pop("cluster_name", None)
        app_name = data.pop("app_name", None)
        result = "error! cluster_name or app_name not found"
        if cluster_name and app_name:
            result = (
                "service created"
                if self._post(
                    f"automation/{cluster_name}/{app_name}/add/service", data
                ).get("name")
                == data["name"]
                else "error! service not created"
            )
        print(result)

    def create_release(self, data):
        cluster_name = data.pop("cluster_name", None)
        app_name = data.pop("app_name", None)
        service_name = data.pop("service_name", None)
        result = "error! cluster_name, app_name or service_name not found"
        if cluster_name and app_name and service_name:
            result = (
                "release created"
                if self._post(
                    f"automation/{cluster_name}/{app_name}/{service_name}/add/release",
                    data,
                ).get("name")
                == data["version"]
                else "error! release not created"
            )
        print(result)

    def delete_application(self, data):
        cluster_name = data.pop("cluster_name", None)
        app_name = data.pop("name", None)
        result = "error! cluster_name or app name not found"
        if cluster_name:
            result = (
                "application deleted"
                if self._delete(f"automation/{cluster_name}/{app_name}").get("app_name")
                == app_name
                else "error! application not deleted"
            )
        print(result)

    def delete_service(self, data):
        cluster_name = data.pop("cluster_name", None)
        app_name = data.pop("app_name", None)
        service_name = data.pop("name", None)
        result = "error! cluster_name, app_name or service name not found"
        if cluster_name and app_name and service_name:
            result = (
                "service deleted"
                if self._delete(
                    f"automation/{cluster_name}/{app_name}/{service_name}"
                ).get("name")
                == service_name
                else "error! service not deleted"
            )
        print(result)

    def remove_resource(self, name: str, id: str):
        if name == "models":
            self._delete(f"intrusion/model/{id}")
        elif name == "traces":
            self._delete(f"traces/{id}")
        print(f"{name[:-1]} deleted")
        return

    def stop_resource(self, name: str, app_name: str, id: str):
        if name == "monitor":
            if not app_name:
                print("app-name not found")
                return
            else:
                self._delete(f"monitoring/{app_name}")

        print(f"{name} stopped")
        return

    def start_monitor(self, data):
        app_name = data.pop("app_name", None)
        monitor_filters = data.pop("monitor_filters", None)
        result = "error! app_name or monitor_filters not found"
        if app_name and monitor_filters:
            result = (
                "monitor started"
                if self._post(
                    f"monitoring/{app_name}",
                    data={"monitor_filters": monitor_filters},
                ).get("status", "")
                == "in_progress"
                else "error! monitor not started"
            )
        print(result)

    def start_training(self, data):
        app_name = data.pop("app_name", None)
        service_name = data.pop("service_name", None)
        ttime = data.pop("ttime", None)
        result = "error! app_name, service_name or ttime not found"
        if app_name and service_name and ttime:
            result = (
                "training started"
                if self._post(
                    f"intrusion/training/{app_name}/{service_name}",
                    data={"ttime": ttime},
                ).get("status", "")
                == "in_progress"
                else "error! training not started"
            )
        print(result)

    def start_detection(self, data):
        app_name = data.pop("app_name", None)
        model_id = data.pop("model_id", None)
        ttime = data.pop("ttime", None)
        result = "error! app_name, model_id or ttime not found"
        if app_name and model_id and ttime:
            result = (
                "detection started"
                if self._post(
                    f"intrusion/detection/{app_name}/{model_id}",
                    data={"ttime": ttime * 60},
                ).get("status", "")
                in ["ready", "running"]
                else "error! detection not started"
            )
        print(result)
