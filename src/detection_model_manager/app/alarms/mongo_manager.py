from bson.objectid import ObjectId
import pymongo


def get_reports_alarms_collection():
    client = pymongo.MongoClient("mongodb://detection_reports_mongo:27017/")
    db = client["reports"]
    return db["alarms"]


def list_alarms(fits: list = []) -> list:
    alarms_collection = get_reports_alarms_collection()
    filters = {}
    if fits:
        filters = fits[0] if len(fits) == 1 else {"$and": fits}

    return alarms_collection.find(filters)


def list_grouped_alarms(
    st_timestamp: int, app_name: str = None, service_name: str = None
) -> list:
    alarms_collection = get_reports_alarms_collection()
    filters = {
        "created_at": {"$gt": st_timestamp},
    }

    if app_name:
        filters["app_name"] = app_name

    if service_name:
        filters["service_name"] = service_name

    alarms = list(
        alarms_collection.aggregate(
            [
                {"$match": filters},
                {"$group": {"_id": "$created_at", "alarms": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
                {"$project": {"timestamp": "$_id", "alarms": 1, "_id": 0}},
            ]
        )
    )

    return {int(a["timestamp"]): a["alarms"] for a in alarms}


def insert_alarms(alarms: list):
    alarms_collection = get_reports_alarms_collection()
    try:
        alarms_collection.insert_many(alarms)
        return True
    except Exception as e:
        pass
    return False
