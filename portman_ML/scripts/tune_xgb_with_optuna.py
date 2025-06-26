import sys
import os
import joblib
import optuna
import traceback
import pandas as pd
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_preprocessing import load_and_preprocess
from portman.config import DATA_PATH
from portman.features import add_engineered_features
from sklearn.preprocessing import LabelEncoder
import numpy as np

# === Load + preprocess (once globally)
df, _ = load_and_preprocess(DATA_PATH)
df = df.sample(n=10000, random_state=42)
df.dropna(subset=["line_profile"], inplace=True)
df = add_engineered_features(df)
df["line_profile"] = pd.to_numeric(df["line_profile"], errors="coerce")
df.dropna(subset=["line_profile"], inplace=True)
df["line_profile"] = df["line_profile"].astype(int)

counts = Counter(df["line_profile"])
valid_classes = [cls for cls, count in counts.items() if count >= 2]
df = df[df["line_profile"].isin(valid_classes)]

X = df.drop(columns=["line_profile", "downstream_snr", "oper_status"], errors="ignore")
y = df["line_profile"]
le = LabelEncoder()
X_train, X_valid, y_train, y_valid = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)
y_train = le.fit_transform(y_train)
y_valid = le.transform(y_valid)

def objective(trial):
    try:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 4, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        }

        model = XGBClassifier(
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            **params
        )
        print("✅ Unique y values:", sorted(y.unique())[:10])
        print(f"🧪 Trial {trial.number} - training with params: {params}")

        model.fit(X_train, y_train)

        mask = np.isin(y_valid, model.classes_)
        X_eval = X_valid[mask]
        y_eval = y_valid[mask]

        if len(y_eval) == 0:
            return 0.0

        preds = model.predict(X_eval)
        return accuracy_score(y_eval, preds)

    except Exception as ex:
        print(f"❌ Error in trial {trial.number}:")
        traceback.print_exc()
        return 0.0

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=1)

print("✅ Best trial:")
print(study.best_trial.params)

best_params = study.best_trial.params
final_model = XGBClassifier(
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42,
    **best_params
)
final_model.fit(X_train, y_train)

output_path = os.path.join("portman", "Portman_ML", "models", "profile_recommender_xgb.pkl")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

joblib.dump(
    {"model": final_model, "classes": final_model.classes_, "label_encoder": le},
    output_path
)

print(f"✅ Model saved to {os.path.abspath(output_path)}")