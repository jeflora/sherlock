def select_data_filters(monitoring_params: list, service_docker_image: str):
    filters = {"container_image_repository": [service_docker_image]}

    if "evt_dir" in monitoring_params:
        filters["evt_dir"] = [">"]

    return filters


def define_processing_technique(algo_details: dict, nreplicas: int) -> str:
    # TODO: Change to lookup dependending on nreplicas...
    return algo_details.get("processing_technique")
