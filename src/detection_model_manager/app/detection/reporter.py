from app.utils import constants
import os


class Report:

    def __init__(self, epoch_size, threshold, interval):
        self.epoch_size = epoch_size
        self.threshold = threshold
        self.interval = interval * constants.SECOND_NANO_SECS
        self.cache = dict()
        self.interval_end = None

    def get_report(self, p_timestamps, p_classifications):
        timestamps = [int(t) for t in (self.cache.get("timestamps", []) + p_timestamps)]
        classifications = self.cache.get("classifications", []) + p_classifications

        if not classifications or not timestamps:
            return []

        remainder = len(classifications) % self.epoch_size

        # Epoch-based Analisys
        ep_classifications, ep_timestamps = [], []
        for idx in range(self.epoch_size, len(classifications), self.epoch_size):
            epoch = classifications[idx - self.epoch_size : idx]

            ep_classifications.append(
                constants.ANOMALY
                if epoch.count(constants.ANOMALY) >= self.threshold
                else constants.NORMAL
            )
            ep_timestamps.append(timestamps[idx])

        self.cache["timestamps"] = timestamps[-remainder:]
        self.cache["classifications"] = classifications[-remainder:]

        ep_timestamps = self.cache.get("ep_timestamps", []) + ep_timestamps
        ep_classifications = (
            self.cache.get("ep_classifications", []) + ep_classifications
        )

        if not ep_timestamps or not ep_classifications:
            return []

        if not self.interval_end:
            self.interval_end = ep_timestamps[0] + self.interval

        # Time-based Analisys
        alarms, st_idx = [], 0
        for idx, item in enumerate(ep_timestamps):
            if item <= self.interval_end:
                continue

            interval_classifications = ep_classifications[st_idx:idx]
            if constants.ANOMALY in interval_classifications:
                alarms.append(
                    {
                        "interval_start": self.interval_end - self.interval,
                        "interval_end": self.interval_end,
                        "ratio": round(
                            float(interval_classifications.count(constants.ANOMALY))
                            / float(len(interval_classifications)),
                            3,
                        ),
                    }
                )
            st_idx = idx
            self.interval_end = self.interval_end + self.interval

        self.cache["ep_timestamps"] = ep_timestamps[st_idx:]
        self.cache["ep_classifications"] = ep_classifications[st_idx:]

        return alarms
