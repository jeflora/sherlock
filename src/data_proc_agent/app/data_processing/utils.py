import hashlib
from pydantic import BaseModel
from typing import Dict, Union, List

from app.data_processing.bridge import (
    CONFIG_FILTERS,
    CONFIG_INDEX_MAP,
    CONFIG_PARAMS,
    CONFIG_TEC_NAME,
    CONFIG_TTIME,
)


class JobRequestBody(BaseModel):
    params: List[str]
    proc_technique: str
    reading_ch: str
    user_filters: Union[Dict[str, List[str]], None] = None
    ttime: int = -1
    index_map_name: str = "syscall_index_map"

    def _hash(self):
        h = hashlib.shake_256()
        h.update(bytes("".join(sorted(self.params)), encoding="utf-8"))
        h.update(bytes(self.proc_technique, encoding="utf-8"))
        h.update(bytes(self.reading_ch, encoding="utf-8"))
        h.update(bytes(str(self.ttime), encoding="utf-8"))
        h.update(bytes(self.index_map_name, encoding="utf-8"))
        if self.user_filters:
            h.update(
                bytes(
                    "".join(
                        sorted(
                            [
                                f"{k}_{''.join(sorted(v))}"
                                for k, v in self.user_filters.items()
                            ]
                        )
                    ),
                    encoding="utf-8",
                )
            )
        return h.hexdigest(12)


class Job:
    def __init__(self, body: JobRequestBody):
        self.request_body = body
        self.uid = self.request_body._hash()
        self.status = "in_progress"

    def done(self):
        self.status = "complete"

    def get_configs(self):
        return (
            self.request_body.reading_ch,
            self.uid,
            {
                CONFIG_TEC_NAME: self.request_body.proc_technique,
                CONFIG_PARAMS: self.request_body.params,
                CONFIG_FILTERS: self.request_body.user_filters,
                CONFIG_INDEX_MAP: self.request_body.index_map_name,
                CONFIG_TTIME: self.request_body.ttime,
            },
        )
