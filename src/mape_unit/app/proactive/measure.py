import requests, time
import multiprocessing as mp


SLEEP_TIME = 55  # seconds
MRI_THRESHOLD_VALUE = 0.750
MRI_MINUTES_COMPUTE = 10


class ProactiveMeasure(mp.Process):

    def __init__(self):
        super().__init__(daemon=True)
        self.should_run = mp.Value("i", 1)

    def run(self):
        while self.should_run.value == 1:
            time.sleep(SLEEP_TIME)

            resp = requests.get(
                "http://detection_model_manager/detection/models/running"
            )
            if resp.status_code >= 400:
                continue

            models_running = resp.json()
            for model_id in models_running:
                resp = requests.get(
                    f"http://metrics_engine/metrics/mri/{model_id}",
                    params={"last_minutes": MRI_MINUTES_COMPUTE},
                )
                if resp.status_code >= 400:
                    continue
                metric_value = resp.json().get("mri").get("value")

                if metric_value < MRI_THRESHOLD_VALUE:
                    self._apply_proactive_measure(model_id)

    def stop_running(self):
        self.should_run.value -= 1

    def _apply_proactive_measure(self, model_id):
        resp = requests.post(f"http://management_engine/measures/proactive/{model_id}")
        return resp.status_code < 400
