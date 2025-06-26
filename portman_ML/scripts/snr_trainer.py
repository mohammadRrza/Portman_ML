import os
import pandas as pd
from portman.config import MODEL_PATH, DATA_PATH
from data_preprocessing import load_and_preprocess
from portman.core.model_trainer import ModelTrainer
from portman.training.trainer_xgb import XGBoostTrainer


class SNRTrainer:
    def __init__(self, strategy=None):
        self.data_path = DATA_PATH
        self.model_path = os.path.join(MODEL_PATH, "snr_risk_model.pkl")
        self.strategy = strategy or XGBoostTrainer(n_estimators=100)

    def add_snr_label(self, df):
        df["low_snr_risk"] = (df["downstream_snr"] < 20).astype(int)
        return df

    def prepare_data(self):
        df, _ = load_and_preprocess(self.data_path)
        df = self.add_snr_label(df)
        return df

    def get_config(self):
        return {
            "target": "low_snr_risk",
            "drop_columns": ["downstream_snr", "oper_status"],
            "model_name": "snr_risk_model.pkl",
            "save_dir": "models",
            "top_k": False,
            "preprocess_fn": self.add_snr_label,
        }

    def run(self):
        df = self.prepare_data()
        config = self.get_config()
        trainer = ModelTrainer(strategy=self.strategy, data=df, config=config)
        trainer.run()
