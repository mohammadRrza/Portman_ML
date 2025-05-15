import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_preprocessing import load_and_preprocess
from portman.training.trainer_rf import RandomForestTrainer
from portman.core.model_trainer import ModelTrainer
from portman.config import DATA_PATH

df, _ = load_and_preprocess(DATA_PATH)

profile_config = {
    "target": "line_profile",
    "drop_columns": ["oper_status", "downstream_snr"],
    "model_name": "profile_recommender.pkl",
    "save_dir": "models",
    "top_k": True
}
trainer = ModelTrainer(strategy=RandomForestTrainer(n_estimators=100), data=df, config=profile_config)
trainer.run()

