import os, redis
from app.algorithms.utils.window import Window
from app.utils import constants, persistence
import app.algorithms.metadata as meta

# ==== ALGOS =====
from app.algorithms.stide_bosc import *

# =================


# ==== STIDE
def get_stide_classifier(window_size: int) -> StideBoSC:
    return StideBoSC(window_size)


# ==== BoSC
def get_bosc_classifier(window_size: int) -> StideBoSC:
    return StideBoSC(window_size, use_bosc=True)


def get_classifier(name: str, window: int):
    clfs = {
        meta.STIDE: get_stide_classifier,
        meta.BOSC: get_bosc_classifier,
    }
    return clfs[name](window) if name in clfs else None


def train_window_based_algorithms(
    out_dir: str,
    model_id: str,
    algo_name: str,
    params: dict,
    redis_incoming_channel: str,
):
    """
    This function trains window-based profiles.
    ===
    {out_dir}: where to store the trained model
    {model_id}: the id of the model
    {algo_name}: the algorithm to use
    {params}: the params for the algorithm
    {redis_incoming_channel}: redis channel to read from
    """

    in_redis_conn = redis.StrictRedis(
        "redis_proc_data", 6379, charset="utf-8", decode_responses=True
    )

    sub = in_redis_conn.pubsub()
    sub.subscribe(redis_incoming_channel)

    win_size = params.get("window", None)
    if not win_size or not isinstance(win_size, int) or win_size < 2:
        return False

    # cut_limit = configuration['algorithm']['cut_limit'] if 'cut_limit' in configuration['algorithm'] else 1.0

    # Initialise timestamps
    # _collect_classifier_timestamp = base_timestamp + (
    #         constants.STORE_MODEL_AT_EACH_HOURS * constants.HOUR_NANO_SECS)
    # _collect_slope_evolution_timestamp = base_timestamp + (
    #         constants.STORE_GROWTH_CURVE_SLOPE * constants.SECOND_NANO_SECS)

    # TODO: Add growth curve
    # seconds_xx = 0
    # growth_dir_path = os.path.join(out_dir, "growth_curve")
    # if not os.path.isdir(growth_dir_path):
    #     os.mkdir(growth_dir_path)
    # slope_growth_curve_out_filename = os.path.join(
    #     growth_dir_path, constants.GROWTH_CURVE_STORE_NAME.format(algo_name, win_size)
    # )

    # if seconds_xx == 0:
    #     with open(slope_growth_curve_out_filename, "w") as evo_fp:
    #         evo_fp.write("0:0\n")
    #     seconds_xx = seconds_xx + constants.STORE_GROWTH_CURVE_SLOPE
    # ==============================================================================

    classifier = get_classifier(algo_name, win_size)
    if classifier is None:
        return False  # ERROR
    
    window = Window(win_size)

    windows = []
    for message in sub.listen():
        if not message or not isinstance(message, dict):
            continue

        data = message.get("data", "")
        if not data or data == 1:
            continue

        if data == "CLOSE":
            if len(windows) > 0:
                classifier.fit(windows)
                windows = []
            break

        for line in data.split("\n"):
            [timestamp, syscall] = line.split()

            if syscall is None:
                continue

            window.add(syscall)
            if window.is_full():
                windows.append(window.get_window())

            if (
                # timestamp >= _collect_slope_evolution_timestamp or
                len(windows) % constants.MAX_WINDOWS
                == 0
            ):
                if len(windows) > 0:
                    classifier.fit(windows)
                    windows = []

            # TODO: Should this be this way? Check for storing growth curve slope evolution
            # if timestamp >= _collect_slope_evolution_timestamp:
            #     db_size = classifier.get_db_size()
            #     with open(slope_growth_curve_out_filename, "a") as evo_fp:
            #         evo_fp.write(f"{str(seconds_xx)}:{str(db_size)}\n")
            #     _collect_slope_evolution_timestamp = (
            #         _collect_slope_evolution_timestamp
            #         + (constants.STORE_GROWTH_CURVE_SLOPE * constants.SECOND_NANO_SECS)
            #     )
            #     seconds_xx = seconds_xx + constants.STORE_GROWTH_CURVE_SLOPE
            # ==============================================================================

    persistence.store_obj(classifier, os.path.join(out_dir, model_id))

    return True
