import datetime
from enum import Enum
import hashlib
import multiprocessing as mp
import redis, pymongo

import app.metrics.window as win


class MonitorStatus(Enum):
    RUNNING = "running"
    COMPLETE = "complete"


class Monitor(mp.Process):

    def __init__(self, operation_mode, model_id, model_details, reading_ch):
        super().__init__()
        self.op_mode = operation_mode
        self.mstatus = MonitorStatus.RUNNING
        self.model_id = model_id
        self.model_details = model_details
        self.reading_channel = reading_ch
        self.should_run = mp.Value("I", 1)

    def stop_monitor(self):
        self.should_run.value -= 1

    def get_data(self):
        return {"model_id": self.model_id, "status": self.mstatus.value}

    def _get_collections(self):
        client = pymongo.MongoClient("mongodb://metrics_engine_mongo:27017/")
        db = client[self.op_mode]

        alphabet_collection = db["alphabet"]
        patterns_collection = db["patterns"]

        if self.op_mode == "training":
            alphabet_collection.delete_many({"model_id": self.model_id})
            patterns_collection.delete_many({"model_id": self.model_id})

        return alphabet_collection, patterns_collection

    def run(self):

        in_redis_conn = redis.StrictRedis(
            "redis_proc_data", 6379, charset="utf-8", decode_responses=True
        )

        sub = in_redis_conn.pubsub()
        sub.subscribe(self.reading_channel)

        alphabet_collection, patterns_collection = self._get_collections()

        window = win.Window(self.model_details["configs"]["window"])

        for message in sub.listen():
            if self.should_run.value != 1:
                break

            if not message or not isinstance(message, dict):
                continue

            data = message.get("data", "")
            if not data or data == 1:
                continue

            if data == "CLOSE":
                break

            # FIXME: For now assumes only window-based algorithms are used
            for line in data.split("\n"):
                [timestamp, syscall] = line.split()

                alphabet_collection.insert_one(
                    {
                        "syscall": syscall,
                        "created_at": datetime.datetime.now(),
                        "model_id": self.model_id,
                        "model_details": self.model_details,
                    }
                )

                window.add(syscall)
                if window.is_full():
                    foo = "".join(window.get_window())
                    pattern = hashlib.sha224(foo.encode("utf-8")).hexdigest()

                    patterns_collection.insert_one(
                        {
                            "pattern": pattern,
                            "created_at": datetime.datetime.now(),
                            "model_id": self.model_id,
                            "model_details": self.model_details,
                        }
                    )

        self.mstatus = MonitorStatus.COMPLETE
