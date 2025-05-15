from abc import ABC, abstractmethod

class TrainingStrategy(ABC):
    @abstractmethod
    def train(self, X, y):
        pass
