import shap
import joblib
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portman.config import MODEL_PATH, DATA_PATH
from data_preprocessing import load_and_preprocess
from portman.explainers.shap_explainer import SHAPExplainer

# Load model and data
bundle = joblib.load(MODEL_PATH + "profile_recommender.pkl")
model = bundle["model"]
classes = bundle["classes"]
df, _ = load_and_preprocess(DATA_PATH)
df.drop(columns=["downstream_snr", "line_profile", "oper_status"], inplace=True, errors="ignore")
sample_df = df.sample(n=5, random_state=42)

# Explain only 1 row
row_index = 0
predicted_label = model.predict(df.iloc[[row_index]])[0]
target_class_index = list(classes).index(predicted_label)

explainer_strategy = SHAPExplainer()
explainer, shap_values = explainer_strategy.explain(model, df)
explainer = shap.Explainer(model, df)
shap_values = explainer(sample_df)

# ✅ Force plot with correct slicing
shap.plots.force(
    explainer.expected_value[target_class_index],
    shap_values[row_index:row_index+1, :, target_class_index],
    df.iloc[row_index]
)
