from app.processing.model import Model
from bson.objectid import ObjectId
import pymongo, datetime


def get_models_meta_collection():
    client = pymongo.MongoClient("mongodb://management_engine_mongo:27017/")
    db = client["detection_models"]
    return db["models_meta"]


def create_model_obj_from_dicto(dicto: dict) -> Model:
    keys_req = [
        "app_name",
        "name",
        "configs",
        "data_processing",
        "service",
        "docker_image",
        "nreplicas",
        "_id",
    ]
    if not dicto or not all(k in dicto for k in keys_req):
        return None

    return Model(
        dicto["app_name"],
        dicto["name"],
        dicto["configs"],
        dicto["data_processing"],
        dicto["service"],
        dicto["docker_image"],
        dicto["nreplicas"],
        _id=str(dicto["_id"]),
    )


def list_models(fits: list = []) -> list:
    meta_collection = get_models_meta_collection()
    filters = {}
    if fits:
        filters = fits[0] if len(fits) == 1 else {"$and": fits}
    return [create_model_obj_from_dicto(d) for d in meta_collection.find(filters)]


def list_model(model_id: str) -> Model:
    meta_collection = get_models_meta_collection()
    details = (
        meta_collection.find_one({"_id": ObjectId(model_id)})
        if ObjectId.is_valid(model_id)
        else None
    )
    return create_model_obj_from_dicto(details) if details else {}


def insert_model(model: Model):
    meta_collection = get_models_meta_collection()
    try:
        meta_collection.insert_one(model.get_mongo_dict())
        return True
    except Exception as e:
        pass
    return False


def delete_model(model_id: str) -> bool:
    meta_collection = get_models_meta_collection()
    if not ObjectId.is_valid(model_id):
        return False
    meta_collection.delete_one({"_id": ObjectId(model_id)})
    return True


#########################
##### Clusters Data #####
#########################


def get_clusters_collection():
    client = pymongo.MongoClient("mongodb://management_engine_mongo:27017/")
    db = client["clusters_metadata"]
    return db["clusters"]


def get_cluster_from_name(cluster_name: str):
    collection = get_clusters_collection()
    obj = collection.find_one({"name": cluster_name}, {"applications": 0, "_id": 0})
    return obj


def get_cluster_name_from_app_name(app_name: str):
    collection = get_clusters_collection()
    obj = collection.find_one(
        {"applications.app_name": app_name}, {"name": 1, "_id": 0}
    )
    return "" if not obj else obj.get("name", "")


def get_cluster_app_names(cluster_name: str):
    names = []
    try:
        names = get_clusters_collection().distinct(
            "applications.app_name", {"name": cluster_name}
        )
    except Exception as e:
        pass
    return names


def insert_cluster(cluster_data: dict):
    try:
        get_clusters_collection().insert_one(cluster_data)
        return {"cluster_name": cluster_data.get("name", "")}
    except Exception as e:
        pass
    return {}


def list_app_details(cluster_name: str, app_name: str):
    try:
        result = get_clusters_collection().find_one(
            {"name": cluster_name, "applications.app_name": app_name},
            {"_id": 0, "applications.$": 1},
        )
        if not result or not result.get("applications", []):
            return {}

        app = result.get("applications")[0]
        return app
    except Exception as e:
        pass
    return {}


def add_app_to_cluster(cluster_name: str, app_to_add: dict):
    try:
        return (
            app_to_add.get("app_name")
            not in get_clusters_collection().distinct("applications.app_name")
            and get_clusters_collection()
            .update_one(
                {"name": cluster_name}, {"$addToSet": {"applications": app_to_add}}
            )
            .modified_count
            != 0
        )
    except Exception as e:
        pass
    return {}


def delete_app_from_cluster(cluster_name: str, app_name: str):
    try:
        get_clusters_collection().update_one(
            {"name": cluster_name}, {"$pull": {"applications": {"app_name": app_name}}}
        )
        return True
    except:
        return False


def list_app_services(cluster_name: str, app_name: str):
    services = []
    try:
        result = (
            get_clusters_collection()
            .aggregate(
                [
                    {
                        "$match": {
                            "name": cluster_name,
                            "applications.app_name": app_name,
                        }
                    },
                    {"$unwind": "$applications"},
                    {"$project": {"_id": 0, "services": "$applications.services"}},
                ]
            )
            .next()
        )

        services = result.get("services", [])
        for srv in services:
            srv["_id"] = str(srv["_id"])
            srv.pop("versions", None)

    except Exception as e:
        pass

    return services


def add_service_to_app(cluster_name: str, app_name: str, service_to_add: dict):
    try:
        get_clusters_collection().update_one(
            {"name": cluster_name, "applications.app_name": app_name},
            {"$addToSet": {"applications.$.services": service_to_add}},
        )
        return True
    except Exception as e:
        pass
    return {}


def delete_service_from_app(cluster_name: str, app_name: str, service_name: str):
    try:
        get_clusters_collection().update_one(
            {"name": cluster_name, "applications.app_name": app_name},
            {"$pull": {"applications.$.services": {"name": service_name}}},
        )
        return True
    except:
        return False


def add_release_to_service(cluster_name, app_name, service_name, new_release):
    try:
        return (
            deactivate_releases_from_service(cluster_name, app_name, service_name)
            and get_clusters_collection()
            .update_one(
                {
                    "name": cluster_name,
                    "applications.app_name": app_name,
                },
                {
                    "$addToSet": {
                        "applications.$[].services.$[service].versions": new_release
                    }
                },
                array_filters=[{"service.name": service_name}],
            )
            .modified_count
            != 0
        )
    except Exception as e:
        pass
    return {}


def get_model_cd_val(model_id: str):
    det_model = list_model(model_id)
    if not det_model:
        return 0.0

    service_details = get_service_monitoring_data(det_model.app_name, det_model.service)
    return service_details["versions"]["mri_cd_component"]


def list_service_releases(cluster_name: str, app_name: str, service_name: str):
    releases = []
    try:
        result = (
            get_clusters_collection().aggregate(
                [
                    {
                        "$match": {
                            "name": cluster_name,
                            "applications.app_name": app_name,
                        }
                    },
                    {"$unwind": "$applications"},
                    {"$unwind": "$applications.services"},
                    {
                        "$match": {
                            "applications.app_name": app_name,
                            "applications.services.name": service_name,
                        }
                    },
                    {"$replaceRoot": {"newRoot": "$applications.services"}},
                    {"$project": {"_id": 0, "versions": "$versions"}},
                ]
            )
        ).next()

        releases = result.get("versions", [])
        for rele in releases:
            rele["_id"] = str(rele["_id"])

    except Exception as e:
        pass

    return releases


def deactivate_releases_from_service(cluster_name, app_name, service_name):
    try:
        get_clusters_collection().update_many(
            {
                "name": cluster_name,
                "applications.app_name": app_name,
            },
            {
                "$set": {
                    "applications.$[].services.$[service].versions.$[].active": False
                }
            },
            array_filters=[{"service.name": service_name}],
        )
        return True
    except Exception as e:
        pass
    return {}


def get_service_monitoring_data(app_name: str, service_name: str) -> dict:
    service = {}
    try:
        cluster_name = get_cluster_name_from_app_name(app_name)
        result = (
            get_clusters_collection().aggregate(
                [
                    {
                        "$match": {
                            "name": cluster_name,
                            "applications.app_name": app_name,
                            "applications.services.name": service_name,
                            "applications.services.versions.active": True,
                        }
                    },
                    {"$unwind": "$applications"},
                    {"$unwind": "$applications.services"},
                    {"$unwind": "$applications.services.versions"},
                    {"$match": {"applications.services.versions.active": True}},
                    {"$project": {"service": "$applications.services", "_id": 0}},
                ]
            )
        ).next()

        service = result.get("service", [])

    except Exception as e:
        pass

    return service


#########################
##### Measures Data #####
#########################
def get_reactive_measures_collection():
    client = pymongo.MongoClient("mongodb://management_engine_mongo:27017/")
    db = client["measures"]
    return db["reactive"]


def get_reactive_measures_actions_collection():
    client = pymongo.MongoClient("mongodb://management_engine_mongo:27017/")
    db = client["measures"]
    return db["actions"]


def add_reactive_measure(model_id: str):
    measure_data = {
        "model_id": model_id,
        "created_at": datetime.datetime.now(),
    }

    try:
        get_reactive_measures_collection().insert_one(measure_data)
        return True
    except Exception as e:
        pass
    return False


def count_reactive_measures(model_id: str, last_minutes: int = 60):
    time_threshold = datetime.datetime.now() - datetime.timedelta(minutes=last_minutes)
    filters = {
        "created_at": {"$gt": time_threshold},
        "model_id": model_id,
    }
    return get_reactive_measures_collection().count_documents(filters)


def add_reactive_measure_execution(
    measure_name: str, model_id: str, app_name: str, service_name: str
):
    measure_action = {
        "name": measure_name,
        "app_name": app_name,
        "service_name": service_name,
        "model_id": model_id,
        "acted_at": datetime.datetime.now(),
    }

    try:
        get_reactive_measures_actions_collection().insert_one(measure_action)
        return True
    except Exception as e:
        pass
    return False


def get_last_action(model_id: str):
    try:
        return (
            get_reactive_measures_actions_collection()
            .find({"model_id": model_id})
            .limit(1)
            .sort([("$natural", -1)])
        ).next()
    except:
        return None


#######################


def delete_cluster(cluster_name: str) -> bool:
    collection = get_clusters_collection()
    collection.delete_one({"name": cluster_name})
    return True
