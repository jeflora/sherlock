import requests, time
import multiprocessing as mp
from collections import Counter


SLEEP_TIME = 55


class ReactiveMeasure(mp.Process):

    def __init__(self):
        super().__init__(daemon=True)
        self.should_run = mp.Value("i", 1)

    def run(self):
        while self.should_run.value == 1:
            time.sleep(SLEEP_TIME)

            alarms = self._polling_alarms()

            if not alarms:
                continue

            counts = Counter([alarm["model_id"] for alarm in alarms])
            for model_id in filter(lambda cnt: counts[cnt] > 0, counts):
                self._apply_reactive_measure(model_id)

    def stop_running(self):
        self.should_run.value -= 1

    def _polling_alarms(self):
        resp = requests.get(
            f"http://detection_model_manager/alarms", params={"last_minutes": 1}
        )
        return resp.json() if resp.status_code < 400 else {}

    def _apply_reactive_measure(self, model_id):
        resp = requests.post(f"http://management_engine/measures/reactive/{model_id}")
        return resp.status_code < 400
