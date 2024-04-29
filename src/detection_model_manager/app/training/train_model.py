import app.training.window_models as win_models
import app.algorithms.metadata as meta
import os


def train_detection_model(model_id, algo_name, algo_params, reading_ch, return_dict):
    out_dir = os.getenv("MODEL_PATH_DIR")
    if algo_name in meta.WINDOW_BASED_ALGOS:
        win_models.train_window_based_algorithms(out_dir, model_id, algo_name, algo_params, reading_ch)
    else:
        return None
