# portman/core/model_trainer.py

import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, top_k_accuracy_score

class ModelTrainer:
    def __init__(self, *, strategy, data, config):
        self.strategy = strategy
        self.df = data
        self.config = config

    def run(self):
        # === Clean and prep ===
        df = self.df.copy()

        if self.config.get("drop_na_target", True):
            df.dropna(subset=[self.config["target"]], inplace=True)

        if "preprocess_fn" in self.config:
            df = self.config["preprocess_fn"](df)

        target = self.config["target"]
        drop_cols = self.config.get("drop_columns", [])

        X = df.drop(columns=[target] + drop_cols, errors='ignore')
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # === Train model ===
        model = self.strategy.train(X_train, y_train)

        # === Filter y_test for known classes (optional for multiclass)
        if hasattr(model, "classes_"):
            mask = y_test.isin(model.classes_)
            X_test = X_test[mask]
            y_test = y_test[mask]

        # === Evaluate ===
        print(f"\n📋 Classification Report for {target}:")
        print(classification_report(y_test, model.predict(X_test)))

        if self.config.get("top_k", False):
            probas = model.predict_proba(X_test)
            topk = top_k_accuracy_score(y_test, probas, k=3, labels=model.classes_)
            print(f"🎯 Top-3 Accuracy: {topk:.2%}")

        # === Save model ===
        os.makedirs(self.config["save_dir"], exist_ok=True)
        path = os.path.join(self.config["save_dir"], self.config["model_name"])
        joblib.dump({"model": model, "classes": getattr(model, "classes_", None)}, path)

        print(f"✅ Model saved to: {path}")
