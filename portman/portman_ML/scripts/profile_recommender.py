import os
import sys
import joblib
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portman.features import add_engineered_features
from portman.config import DATA_PATH, MODEL_PATH
from scripts.data_preprocessing import load_and_preprocess
from dj_bridge import DSLAMPort
from collections import Counter

class ProfileRecommender:
    def __init__(self, data_path=DATA_PATH, model_path=MODEL_PATH):
        self.data_path = data_path
        self.model_path = model_path
        self.label_encoder = LabelEncoder()
        self.model = None

    def load_and_prepare_data(self):
        df, _ = load_and_preprocess(self.data_path)
        df = add_engineered_features(df)
        df.dropna(subset=["line_profile"], inplace=True)

        df["line_profile"] = pd.to_numeric(df["line_profile"], errors="coerce")
        df.dropna(subset=["line_profile"], inplace=True)
        df["line_profile"] = df["line_profile"].astype(int)
        df["line_profile"] = self.label_encoder.fit_transform(df["line_profile"])

        X = df.drop(columns=["line_profile", "downstream_snr", "oper_status"], errors="ignore")
        y = df["line_profile"]
        counts = Counter(y)
        valid_classes = [cls for cls, count in counts.items() if count >= 2]
        mask = y.isin(valid_classes)
        X = X[mask]
        y = y[mask]
        return train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

    def train(self, X_train, X_test, y_train, y_test, n_estimators=100, max_depth=5):
        self.model = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            eval_metric="mlogloss"
        )
        
        le = LabelEncoder()
        y_train = le.fit_transform(y_train)
        y_valid = le.transform(y_test)
        self.model.fit(X_train, y_train)

    def evaluate(self, X_test, y_test):
        y_pred = self.model.predict(X_test)
        print("=== Classification Report ===")
        print(classification_report(y_test, y_pred))

    def save_model(self, filename="profile_recommender_xgb.pkl"):
        os.makedirs(self.model_path, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "classes": self.model.classes_,
            "label_encoder": self.label_encoder
        }, os.path.join(self.model_path, filename))
        print(f"✅ Model saved to {os.path.join(self.model_path, filename)}")

    def predict_new(self, new_data: pd.DataFrame, output_path="predictions.csv"):
        preds = self.model.predict(new_data)
        decoded = self.label_encoder.inverse_transform(preds)
        pd.DataFrame({"prediction": decoded}).to_csv(output_path, index=False)
        print(f"✅ Predictions saved to {output_path}")

    def load_and_prepare_data_2(self):
        qs = DSLAMPort.objects.filter(downstream_snr__isnull=False)
        df = pd.DataFrame.from_records(qs.values())

        df = add_engineered_features(df)
        df.dropna(subset=["line_profile"], inplace=True)

        df["line_profile"] = pd.to_numeric(df["line_profile"], errors="coerce")
        df.dropna(subset=["line_profile"], inplace=True)
        df["line_profile"] = df["line_profile"].astype(int)
        df["line_profile"] = self.label_encoder.fit_transform(df["line_profile"])

        X = df.drop(columns=["line_profile", "downstream_snr", "oper_status"], errors="ignore")
        y = df["line_profile"]

        return train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)