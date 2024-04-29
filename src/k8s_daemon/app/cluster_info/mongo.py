import pymongo


def get_clusters_collection():
    client = pymongo.MongoClient("mongodb://k8s_daemon_mongo:27017/")
    db = client["kubernetes"]
    return db["clusters"]


def insert_cluster_data(cluster_data):
    clusters_collection = get_clusters_collection()
    try:
        result = clusters_collection.insert_one(cluster_data)
        return str(result.inserted_id) if result else None
    except Exception as e:
        pass
    return None


def get_cluster_data(cluster_name: str) -> dict:
    clusters_collection = get_clusters_collection()
    cluster_data = clusters_collection.find_one({"name": cluster_name})

    if cluster_data:
        cluster_data["_id"] = str(cluster_data["_id"])
        cluster_data["ca_filepath"] = f"/crt_files/{cluster_data['ca_file']}"

    return {} if not cluster_data else cluster_data


def get_clusters() -> list:
    clusters_collection = get_clusters_collection()

    clusters = []
    for obj in clusters_collection.find({}):
        clusters.append(obj)
        clusters[-1]["_id"] = str(clusters[-1]["_id"])

    return clusters


def delete_cluster_data(cluster_name: str) -> bool:
    clusters_collection = get_clusters_collection()
    clusters_collection.delete_one({"name": cluster_name})
    return True
