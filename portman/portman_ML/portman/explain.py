import shap
import pandas as pd
import matplotlib.pyplot as plt
import joblib

def load_model(path):
    """Load a trained model (joblib format)."""
    return joblib.load(path)

def explain_model_global(model, X, max_display=10):
    """
    Show a SHAP summary plot (beeswarm or bar) of feature importance.
    """
    explainer = shap.Explainer(model)
    shap_values = explainer(X)

    shap.summary_plot(shap_values, X, max_display=max_display)

def explain_model_force(model, X, row_index=0, output_html=None):
    """
    Show or save a SHAP force plot for a single row.
    """
    explainer = shap.Explainer(model)
    shap_values = explainer(X)

    force_plot = shap.plots.force(
        explainer.expected_value,
        shap_values[row_index],
        X.iloc[row_index]
    )

    if output_html:
        shap.save_html(output_html, force_plot)
    else:
        force_plot.show()

def get_shap_dataframe(model, X):
    """
    Return a DataFrame of SHAP values per feature.
    """
    explainer = shap.Explainer(model)
    shap_values = explainer(X)
    return pd.DataFrame(shap_values.values, columns=X.columns)
