import hashlib
from bson.objectid import ObjectId


class Model:

    def __init__(self, app_name, name, configs, data_proc, service_name, doc_img, nrep, _id=None):
        self.app_name = app_name
        self.name = name
        self.configs = configs
        self.data_processing = data_proc
        self.service = service_name
        self.docker_image = doc_img
        self.nreplicas = nrep
        self.model_id = self._hash() if not _id else _id

    def _hash(self):
        h = hashlib.shake_256()
        h.update(bytes(self.app_name, encoding="utf-8"))
        h.update(bytes(self.name, encoding="utf-8"))
        h.update(
            bytes(
                "".join([f"{k}__{v}" for k, v in self.configs.items()]),
                encoding="utf-8",
            )
        )
        h.update(bytes(self.data_processing, encoding="utf-8"))
        h.update(bytes(self.service, encoding="utf-8"))
        h.update(bytes(self.docker_image, encoding="utf-8"))
        h.update(bytes(f"{self.nreplicas}", encoding="utf-8"))
        return h.hexdigest(12)  # Digest with length 24

    def get_id(self):
        return self.model_id

    def get_mongo_dict(self):
        return {
            "app_name": self.app_name,
            "name": self.name,
            "configs": self.configs,
            "data_processing": self.data_processing,
            "service": self.service,
            "docker_image": self.docker_image,
            "nreplicas": self.nreplicas,
            "_id": ObjectId(self.model_id),
        }
