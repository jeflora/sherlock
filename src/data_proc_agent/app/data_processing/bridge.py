import redis, datetime
import os, sqlite3, contextlib
import app.data_processing.techniques as techniques

CONFIG_FILTERS = "filters"
CONFIG_TEC_NAME = "technique_name"
CONFIG_PARAMS = "params"
CONFIG_INDEX_MAP = "index_map"
CONFIG_TTIME = "ttime"
CONFIG_REQ_FIELDS = [
    CONFIG_FILTERS,
    CONFIG_TEC_NAME,
    CONFIG_PARAMS,
    CONFIG_INDEX_MAP,
    CONFIG_TTIME,
]


def process_data_traces(
    redis_incoming_channel: str,
    redis_outgoing_channel: str,
    processing_config: dict,
    return_dict=None,
):
    """
    Processes data according to different techniques and configuration defined
    {redis_incoming_channel}: Redis reading channel from daemonset
    {redis_outgoing_channel}: Redis writing channel to forward data to detection models/algorithms
    {processing_config}: configuration of the data processing technique to be used. contains:
        'technique_name': (str) key to refer to data processing technique
        'params': (list) incoming data format (params of sysdig)
        'filters': (dicto) {'param_name': [list of accepable values]} filters to be applied
            (e.g., select data from a service through docker image name)
        'ttime': (int) time (in seconds) that the data should be passed on to the queue
        'index_map': (str) name of the index_map to be used
    {return_dict}, optional: used to return data to main process, if needed
    """

    if not all(f in processing_config for f in CONFIG_REQ_FIELDS):
        return False

    in_redis_conn = redis.StrictRedis(
        "redis_pubsub_traces", 6379, charset="utf-8", decode_responses=True
    )

    out_redis_conn = redis.StrictRedis(
        "redis_proc_data", 6379, charset="utf-8", decode_responses=True
    )

    sub = in_redis_conn.pubsub()
    sub.subscribe(redis_incoming_channel)

    index_map = get_index_map(processing_config[CONFIG_INDEX_MAP])

    cache = None
    stop_time = (
        datetime.datetime.now()
        + datetime.timedelta(seconds=processing_config[CONFIG_TTIME])
        if processing_config[CONFIG_TTIME] != -1
        else None
    )
    for message in sub.listen():
        if message is not None and isinstance(message, dict):
            data = message.get("data", "")
            if not data or data == 1:
                continue

            closing = data == "CLOSE" or (
                stop_time and datetime.datetime.now() >= stop_time
            )
            processed_data, cache = techniques.process_data(
                processing_config[CONFIG_TEC_NAME],
                processing_config[CONFIG_PARAMS],
                processing_config[CONFIG_FILTERS],
                data,
                index_map,
                cache=cache,
                closing=closing,
            )

            if closing:
                if processed_data:
                    out_redis_conn.publish(redis_outgoing_channel, processed_data)
                out_redis_conn.publish(redis_outgoing_channel, "CLOSE")
                break

            if not processed_data:
                continue

            # Write forward
            out_redis_conn.publish(redis_outgoing_channel, processed_data)

    return True


def get_index_map(name: str) -> dict:
    index_map_path = os.getenv("INDEX_MAP_DIR")
    dbfile = os.path.join(index_map_path, f"{name}.db")
    index_map = {}
    with contextlib.closing(sqlite3.connect(dbfile)) as conn:
        with conn as cur:
            data = cur.execute("SELECT syscall, value FROM INDEX_MAP").fetchall()
            for item in data:
                (k, v) = item
                index_map[k] = v
    return index_map