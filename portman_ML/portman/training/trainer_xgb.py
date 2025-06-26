from xgboost import XGBClassifier
from .strategy_base import TrainingStrategy

class XGBoostTrainer(TrainingStrategy):
    def __init__(self, **kwargs):
        self.model = XGBClassifier(
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            **kwargs
        )

    def train(self, X, y):
        return self.model.fit(X, y)
