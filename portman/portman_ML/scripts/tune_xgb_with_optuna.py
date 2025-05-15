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

# === Load + preprocess
df, _ = load_and_preprocess(DATA_PATH)
df.dropna(subset=["line_profile"], inplace=True)
df = add_engineered_features(df)

# === Drop rare classes before splitting
y = df["line_profile"]
counts = Counter(y)
valid_classes = [cls for cls, count in counts.items() if count >= 2]
df = df[df["line_profile"].isin(valid_classes)]

# === Define X and y
X = df.drop(columns=["line_profile", "downstream_snr", "oper_status"], errors="ignore")
y = df["line_profile"]


# === Stratified split
X_train, X_valid, y_train, y_valid = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

# === Optuna tuning
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
        model.fit(X_train, y_train)

        # Filter evaluation set to only seen classes
        known_classes = set(model.classes_)
        mask = y_valid.isin(known_classes)
        X_eval = X_valid[mask]
        y_eval = y_valid[mask]

        if len(y_eval) == 0:
            return 0.0

        preds = model.predict(X_eval)
        return accuracy_score(y_eval, preds, labels=model.classes_)

    except Exception:
        print(f"❌ Error in trial {trial.number}:")
        traceback.print_exc()
        return 0.0

# === Run study
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=25)

# === Report best result
print("✅ Best trial:")
print(study.best_trial.params)

# # === Train final model
# best_params = study.best_trial.params
# final_model = XGBClassifier(
#     use_label_encoder=False,
#     eval_metric="mlogloss",
#     random_state=42,
#     **best_params
# )
# final_model.fit(X_train, y_train)

# # === Save model
# os.makedirs("models", exist_ok=True)
# joblib.dump(
#     {"model": final_model, "classes": final_model.classes_},
#     "models/profile_recommender_xgb.pkl"
# )
# print("✅ Final tuned XGBoost model saved to models/profile_recommender_xgb.pkl")
