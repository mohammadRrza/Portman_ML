import os
import sys
import shap
import pandas as pd
import joblib
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portman.config import MODEL_PATH, DATA_PATH
from data_preprocessing import load_and_preprocess

# === Load model ===
model = joblib.load(MODEL_PATH + "snr_risk_model.pkl")

# === Load and preprocess data ===
df, _ = load_and_preprocess(DATA_PATH)

# Recreate label: low SNR risk
df['low_snr_risk'] = (df['downstream_snr'] < 20).astype(int)
df.drop(columns=["downstream_snr", "oper_status", "low_snr_risk"], inplace=True, errors='ignore')

# === Sample a smaller set for visualization ===
df_sample = df.sample(n=100, random_state=42)

# === Create SHAP explainer ===
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(df_sample)

# === Summary Plot ===
shap.plots.bar(shap_values)

# Optional: Detailed plot for one row
# shap.force_plot(explainer.expected_value[1], shap_values[1][0], df_sample.iloc[0], matplotlib=True)
