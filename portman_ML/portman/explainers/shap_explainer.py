import shap
from .strategy_base import ExplainerStrategy

class SHAPExplainer(ExplainerStrategy):
    def explain(self, model, X):
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)
        return explainer, shap_values
