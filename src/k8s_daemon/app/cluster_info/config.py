import kubernetes as k8s

import app.cluster_info.mongo as mongo


def get_cluster_config(cluster_id_name: str):
    cluster_data = mongo.get_cluster_data(cluster_id_name)
    if not cluster_data:
        return None

    configuration = k8s.client.Configuration()
    configuration.assert_hostname = False
    configuration.api_key["authorization"] = cluster_data.get("api_token")
    configuration.api_key_prefix["authorization"] = "Bearer"
    configuration.host = (
        f'https://{cluster_data.get("hostname")}:{cluster_data.get("port")}'
    )
    configuration.ssl_ca_cert = cluster_data.get("ca_filepath")

    return configuration


def get_corev1_api_client(cluster_id_name: str):
    config = get_cluster_config(cluster_id_name)
    if not config:
        return None
    api_client = k8s.client.ApiClient(config)
    return k8s.client.CoreV1Api(api_client)


def get_appsv1_api_client(cluster_id_name: str):
    config = get_cluster_config(cluster_id_name)
    if not config:
        return None
    api_client = k8s.client.ApiClient(config)
    return k8s.client.AppsV1Api(api_client)
