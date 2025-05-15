import pandas as pd
import joblib
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portman.config import MODEL_PATH, NEW_DATA_PATH
from data_preprocessing import load_and_preprocess


# === Load model and known classes ===
bundle = joblib.load(MODEL_PATH + 'profile_recommender.pkl')
model = bundle["model"]
profile_classes = bundle["classes"]

# === Load and preprocess new port data ===
df, _ = load_and_preprocess(NEW_DATA_PATH)

# === Drop any target columns if present ===
df.drop(columns=["line_profile", "oper_status", "downstream_snr"], inplace=True, errors='ignore')

# === Predict profile probabilities ===
probas = model.predict_proba(df)

# === Get top 3 recommendations per row ===
top_k = 3
top3_indices = probas.argsort(axis=1)[:, -top_k:][:, ::-1]

print("🔧 Recommended DSL Line Profiles for New Ports:")
for i, row_indices in enumerate(top3_indices):
    print(f"\nRow {i+1} Recommendations:")
    for rank, class_index in enumerate(row_indices):
        profile = profile_classes[class_index]
        confidence = probas[i][class_index]
        print(f"  Top {rank + 1}: Profile {profile} (Confidence: {confidence:.2%})")
