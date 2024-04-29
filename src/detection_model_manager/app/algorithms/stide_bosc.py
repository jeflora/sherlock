import hashlib
from collections import Counter

from app.utils import constants


class StideBoSC:

    def __init__(self, window_size: int, use_bosc=False):
        self.behaviour_db = dict()
        self.window_size = window_size
        self.using_BoSC = use_bosc

    def predict(self, trace: list) -> list:
        return self._hash_predict(trace)

    def fit(self, trace: list):
        self._hash_train(trace)
        return

    def get_db_size(self):
        count = 0
        for key in self.behaviour_db:
            count += len(self.behaviour_db[key])
        return count

    def _produce_bosc(self, window: list) -> str:
        counter = Counter(window)

        keys = sorted(counter.elements())

        results = list()
        for key in keys:
            temp = str(key) + "," + str(counter[key])
            results.append(temp)

        return "|".join(results)

    def _hash_train(self, trace: list):
        if len(trace) == 0:
            return

        for window in trace:
            first = str(window[0])

            if first not in self.behaviour_db.keys():
                self.behaviour_db[first] = set()

            if self.using_BoSC:
                foo = self._produce_bosc(window)
            else:
                foo = ",".join([str(i) for i in window[1:]])
            hash_value = hashlib.sha224(foo.encode("utf-8")).hexdigest()
            self.behaviour_db[first].add(hash_value)

        return

    def _hash_predict(self, trace: list) -> list:
        result = []

        for window in trace:
            first = str(window[0])

            if first not in self.behaviour_db.keys():
                result.append(constants.ANOMALY)
                continue

            if self.using_BoSC:
                foo = self._produce_bosc(window)
            else:
                foo = ",".join([str(i) for i in window[1:]])
            hash_value = hashlib.sha224(foo.encode("utf-8")).hexdigest()

            anomaly = hash_value not in self.behaviour_db[first]

            result.append(constants.ANOMALY if anomaly else constants.NORMAL)

        return result
