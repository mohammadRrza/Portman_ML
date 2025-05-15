import joblib
import pandas as pd
from portman.preprocessing import load_and_preprocess

def load_model(path):
    """Load a model from file."""
    return joblib.load('portman_ML\models\snr_risk_model.pkl')

def predict_from_csv(model_path, csv_path, drop_columns=None):
    """Load data, preprocess, predict risk or class label."""
    model = load_model(model_path + 'snr_risk_model.pkl')
    df, _ = load_and_preprocess(csv_path)

    # Drop target or leaking columns if needed
    if drop_columns:
        df.drop(columns=drop_columns, inplace=True, errors='ignore')

    preds = model.predict(df)
    return preds, df

def predict_probabilities(model_path, csv_path, drop_columns=None):
    """Return class probabilities from a model."""
    model = load_model(model_path)
    df, _ = load_and_preprocess(csv_path)

    if drop_columns:
        df.drop(columns=drop_columns, inplace=True, errors='ignore')

    probas = model.predict_proba(df)
    return probas, df
