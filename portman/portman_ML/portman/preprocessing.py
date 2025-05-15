import os
import sys
import joblib
from matplotlib import pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portman.config import LOW_SNR_THRESHOLD, DATA_PATH

from data_preprocessing import load_and_preprocess

def parse_uptime(uptime_str):
    """Convert 'HH:MM:SS' uptime to seconds."""
    try:
        parts = uptime_str.split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        return 0

def load_data(filepath: str) -> pd.DataFrame:
    """Load CSV file with low-memory flag."""
    return pd.read_csv(filepath, low_memory=False)

def preprocess(df: pd.DataFrame, target: str = None, model_path: str = ""):
    # === Load and preprocess data ===
    df, _ = load_and_preprocess(DATA_PATH)

    # === Create target: low SNR risk (1 = low downstream SNR < 20 dB) ===
    df['low_snr_risk'] = (df['downstream_snr'] < LOW_SNR_THRESHOLD).astype(int)

    # === Drop columns that leak or are irrelevant ===
    df.drop(columns=['downstream_snr', 'low_snr_risk'], inplace=False)  # kept downstream_snr for label only

    # === Define features and target ===
    X = df.drop(columns=['downstream_snr', 'low_snr_risk'], errors='ignore')
    X = df.drop(columns=['downstream_snr', 'low_snr_risk', 'oper_status'], errors='ignore')

    y = (df['downstream_snr'] < LOW_SNR_THRESHOLD).astype(int)  # Recompute to ensure alignment

    # === Split data ===
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # === Train model ===
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # === Evaluate model ===
    y_pred = model.predict(X_test)
    print("=== Classification Report (Low SNR Risk) ===")
    print(classification_report(y_test, y_pred))

    # === Show confusion matrix ===
    disp = ConfusionMatrixDisplay.from_estimator(model, X_test, y_test, cmap="Blues", values_format="d")
    plt.title("Confusion Matrix: Low SNR Risk")
    plt.show()

    # === Save model ===
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "portman_ML/models/snr_risk_model.pkl")
    print("✅ SNR Risk Model saved to portman_ML/models/snr_risk_model.pkl")


