from typing import Optional
from api_client.api_client import APIClient
import typer, configparser, yaml

app = typer.Typer()

config = configparser.ConfigParser()
config.read("config.ini")
api_client = APIClient(config["api_server"]["url"])


create_operations = {
    "cluster": api_client.create_cluster,
    "application": api_client.create_application,
    "service": api_client.create_service,
    "release": api_client.create_release,
}

delete_operations = {
    "application": api_client.delete_application,
    "service": api_client.delete_service,
}

start_operations = {
    "monitor": api_client.start_monitor,
    "training": api_client.start_training,
    "detection": api_client.start_detection,
}


@app.command("create")
def create(filename: str):
    """
    Create a resource from a file
    """
    with open(filename) as f:
        for doc in yaml.safe_load_all(f):
            for key in doc:
                if key not in create_operations:
                    print(f"object {key} not recognized")
                    continue
                create_operations[key](doc[key])


@app.command()
def get(
    cluster_name: str,
    name: str,
    namespace: Optional[str] = "default",
    app_name: Optional[str] = "",
    service_name: Optional[str] = "",
):
    """
    Display one or many resources
      e.g.,:
      usherlock get <cluster_name> services
    """
    k8s_no_ns = ["k8s_nodes", "k8s_namespaces"]
    k8s_namespaced = ["k8s_daemonsets", "k8s_deployments", "k8s_services", "k8s_pods"]
    usherlock_resources = [
        "certificates",
        "cluster",
        "application",
        "service",
        "release",
        "monitoring",
        "models",
        "traces",
    ]

    if name in k8s_no_ns:
        api_client.get_resources_list(cluster_name, name[4:])
    elif name in k8s_namespaced:
        api_client.get_namespaced_resources_list(cluster_name, namespace, name[4:])
    elif name in usherlock_resources:
        api_client.get_cluster_resources(
            name, cluster_name, namespace, app_name, service_name
        )
    else:
        print(f"error: the server does not have a resource type {name}")

    return


@app.command()
def start(filename: str):
    """
    Start resources from a file
    """
    with open(filename) as f:
        for doc in yaml.safe_load_all(f):
            for key in doc:
                if key not in start_operations:
                    print(f"object {key} not recognized")
                    continue
                start_operations[key](doc[key])


@app.command()
def stop(name: str, app_name: Optional[str] = "", id: Optional[str] = ""):
    resources = ["monitor"]
    if name not in resources:
        print(f"error: cannot remove resource type {name}")
        return
    api_client.stop_resource(name, app_name, id)


# @app.command()
# def update(cluster_name: str, name: str, namespace: Optional[str] = "default"):
#     """
#     Update a resource on the server
#     """
#     pass


@app.command()
def remove(
    name: str,
    id: str,
):
    resources = ["models", "traces"]
    if name not in resources:
        print(f"error: cannot remove resource type {name}")
        return
    api_client.remove_resource(name, id)


@app.command()
def delete(filename: str):
    """
    Delete resources from a file
    """
    with open(filename) as f:
        for doc in yaml.safe_load_all(f):
            for key in doc:
                if key not in delete_operations:
                    print(f"object {key} not recognized")
                    continue
                delete_operations[key](doc[key])


if __name__ == "__main__":
    app()
