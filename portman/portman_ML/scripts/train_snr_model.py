import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_preprocessing import load_and_preprocess
from portman.config import MODEL_PATH, DATA_PATH
from portman.training.trainer_rf import RandomForestTrainer
from portman.core.model_trainer import ModelTrainer
from portman.training.trainer_xgb import XGBoostTrainer

df, _ = load_and_preprocess(DATA_PATH)
df["low_snr_risk"] = (df["downstream_snr"] < 20).astype(int)
X = df.drop(columns=["downstream_snr", "low_snr_risk", "oper_status"], errors="ignore")
y = df["low_snr_risk"]

def add_snr_label(df):
    df["low_snr_risk"] = (df["downstream_snr"] < 20).astype(int)
    return df

snr_config = {
    "target": "low_snr_risk",
    "drop_columns": ["oper_status", "downstream_snr"],
    "model_name": "snr_risk_model.pkl",
    "save_dir": "models",
    "top_k": False,
    "preprocess_fn": add_snr_label
}


trainer = ModelTrainer(strategy=XGBoostTrainer(n_estimators=100), data=df, config=snr_config)
trainer.run()
