import pymongo, datetime, requests
from py_stringmatching.similarity_measure.tversky_index import TverskyIndex


# Metric weights as defined in paper:
### [1] J. Flora, N. Antunes, Towards a metric for reuse of microservice intrusion detection models,
###     in: 2024 19th European Dependable Computing Conference (EDCC), 2024.
MRI_WEIGHTS = [0.15, 0.25, 0.60]


def compute_metric(model_id: str, minutes: int):
    client = pymongo.MongoClient("mongodb://metrics_engine_mongo:27017/")

    cut_date = datetime.datetime.now() - datetime.timedelta(minutes=minutes)

    train_alphabet, train_patterns = get_data(
        client["training"], {"model_id": model_id}
    )
    detection_alphabet, detection_patterns = get_data(
        client["detection"],
        {"$and": [{"model_id": model_id}, {"created_at": {"$gte": cut_date}}]},
    )

    cd_component = get_source_code_component(model_id)
    al_component = get_similarity(train_alphabet, detection_alphabet)
    ri_component = get_similarity(train_patterns, detection_patterns)

    ## See [1]
    mri = (
        cd_component * MRI_WEIGHTS[0]
        + al_component * MRI_WEIGHTS[1]
        + ri_component * MRI_WEIGHTS[2]
    )

    return mri


def get_similarity(setA, setB):
    # See [1]
    tvi = TverskyIndex(alpha=0.1, beta=0.9)
    return tvi.get_raw_score(setA, setB)


def get_data(database, filters={}):
    alphabet_collection = database["alphabet"]
    patterns_collection = database["patterns"]

    alphabet = alphabet_collection.find(filters).distinct("syscall")
    patterns = patterns_collection.find(filters).distinct("pattern")

    return alphabet, patterns


def get_source_code_component(model_id: str):
    resp = requests.get(
        f"http://management_engine/models/{model_id}/metrics/mri/cd_component"
    )
    if not resp or not resp.json().get("cd", None) == None:
        return 1.0
    return resp.get("cd")
