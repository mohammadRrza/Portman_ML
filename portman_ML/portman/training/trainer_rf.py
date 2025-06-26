from sklearn.ensemble import RandomForestClassifier
from .strategy_base import TrainingStrategy

class RandomForestTrainer(TrainingStrategy):
    def __init__(self, **kwargs):
        self.model = RandomForestClassifier(**kwargs)

    def train(self, X, y):
        return self.model.fit(X, y)
