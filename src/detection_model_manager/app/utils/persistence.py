from app.utils import constants
import pickle


def store_obj(obj, out_filename: str):
    with open(out_filename, "wb") as fp:
        pickle.dump(obj, fp, protocol=pickle.HIGHEST_PROTOCOL)


def load_obj(filename: str):
    with open(filename, "rb") as fp:
        obj = pickle.load(fp)
    return obj
