import multiprocessing as mp
from enum import Enum
import os, redis, datetime

from app.utils import constants, persistence
import app.algorithms.metadata as meta
import app.detection.reporter as rep
from app.algorithms.utils.window import Window
import app.alarms.mongo_manager as mongo


class ModelStatus(Enum):
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    COMPLETE = "complete"


class DetectionModel(mp.Process):

    def __init__(
        self, model_id: str, reading_ch: str, app_name: str, service_name: str
    ):
        super().__init__()
        self.app_name = app_name
        self.service_name = service_name
        self.mstatus = ModelStatus.STARTING
        self.detmodel_id = model_id
        self.reading_ch = reading_ch
        self.det_model = self._get_detection_model()
        self.mstatus = ModelStatus.READY
        self.detection_running = mp.Value("i", 0)

    def get_data(self):
        return {"model_id": self.detmodel_id, "status": self.mstatus.value}

    def stop_detection(self):
        self.detection_running.value += 1

    def _get_detection_model(self):
        return persistence.load_obj(
            os.path.join(
                os.getenv("MODEL_PATH_DIR"),
                self.detmodel_id,
            )
        )

    def run(self):
        self.mstatus = ModelStatus.RUNNING

        in_redis_conn = redis.StrictRedis(
            "redis_proc_data", 6379, charset="utf-8", decode_responses=True
        )

        sub = in_redis_conn.pubsub()
        sub.subscribe(self.reading_ch)

        reporter = rep.Report(
            constants.EPOCH_SIZE, constants.DET_THRESHOLD, constants.TIME_INTERVAL
        )

        cache = None
        for message in sub.listen():
            if self.detection_running.value != 0:
                break

            if not message or not isinstance(message, dict):
                continue

            data = message.get("data", "")
            if not data or data == 1:
                continue

            if data == "CLOSE":
                break

            timestamps, data_to_classify, cache = self._process_data(data, cache)
            classifications = self.det_model.predict(data_to_classify)

            alarms = reporter.get_report(timestamps, classifications)
            if not alarms:
                continue

            for alarm in alarms:
                alarm["model_id"] = self.detmodel_id
                alarm["app_name"] = self.app_name
                alarm["service_name"] = self.service_name
                alarm["created_at"] = int(datetime.datetime.now().timestamp())

            if not mongo.insert_alarms(alarms):
                pass  # TODO: Add logging...

        self.mstatus = ModelStatus.COMPLETE
        return

    def _process_data(self, data, cache):
        class_name = str(type(self.det_model).__name__).lower()
        return (
            self._process_data_window(data, cache)
            if any(a in class_name for a in meta.WINDOW_BASED_ALGOS)
            else self._process_data_ml(data, cache)
        )

    def _process_data_window(self, data, cache):
        cache = dict() if cache is None else cache
        window = cache.get("window", Window(self.det_model.window_size))
        timestamps = cache.get("timestamps", [])
        windows = []

        for line in data.split("\n"):
            [timestamp, syscall] = line.split()

            timestamps.append(timestamp)
            window.add(syscall)
            if window.is_full():
                windows.append(window.get_window())

        cache["window"] = window
        cache["timestamps"] = timestamps[len(windows) :]

        return timestamps[: len(windows)], windows, cache

    def _process_data_ml(self, data, cache):
        return None, None, cache
