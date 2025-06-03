# portman_ml/jobs/train_model.py

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

from dslam.models import DSLAMPort  # adjust as needed
from portman.config import MODEL_PATH


def run():
    print("Starting model training job...")

    # Load data from ORM
    queryset = DSLAMPort.objects.all().values()
    df = pd.DataFrame(list(queryset))
    df.dropna(subset=["downstream_snr", "line_profile"], inplace=True)

    # Target
    df["low_snr_risk"] = (df["downstream_snr"] < 20).astype(int)

    # Encode line profile
    le = LabelEncoder()
    df["line_profile"] = pd.to_numeric(df["line_profile"], errors="coerce")
    df.dropna(subset=["line_profile"], inplace=True)
    df["line_profile"] = df["line_profile"].astype(int)
    df["line_profile"] = le.fit_transform(df["line_profile"])

    X = df.drop(columns=["downstream_snr", "low_snr_risk", "oper_status"], errors="ignore")
    y = df["line_profile"]

    # Check label balance
    if y.value_counts().min() < 2:
        print("❌ Not enough samples per class.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

    model = XGBClassifier(n_estimators=100, max_depth=5, random_state=42, eval_metric="mlogloss")
    model.fit(X_train, y_train)

    print(classification_report(y_test, model.predict(X_test)))

    os.makedirs(MODEL_PATH, exist_ok=True)
    joblib.dump({
        "model": model,
        "label_encoder": le
    }, os.path.join(MODEL_PATH, "profile_recommender_xgb.pkl"))

    print("✅ Model saved to:", os.path.join(MODEL_PATH, "profile_recommender_xgb.pkl"))
