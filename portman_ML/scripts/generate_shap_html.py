import os
import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portman.features import add_engineered_features
from data_preprocessing import load_and_preprocess
from portman.config import DATA_PATH, MODEL_PATH

df, _ = load_and_preprocess(DATA_PATH)
df = add_engineered_features(df)
X = df.drop(columns=["line_profile", "downstream_snr", "oper_status"], errors="ignore")

bundle = joblib.load(os.path.join(MODEL_PATH, "profile_recommender_xgb.pkl"))
model = bundle["model"]

explainer = shap.Explainer(model)
shap_values = explainer(X)

output_dir = "shap_html"
os.makedirs(output_dir, exist_ok=True)

print("Generating SHAP force plots...")
for i in range(min(10, len(X))):
    html_path = os.path.join(output_dir, f"shap_port_{i+1}.html")
    shap.save_html(html_path, shap.plots.force(
        explainer.expected_value,
        shap_values[i],
        X.iloc[i],
        matplotlib=False
    ))
    print(f"✅ Saved: {html_path}")