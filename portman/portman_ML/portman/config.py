import os
from dotenv import load_dotenv

# Load .env file from root directory
load_dotenv()

# === File paths ===
DATA_PATH = os.getenv("DATA_PATH", "portman_ML/data/dslam_dslamport.csv")
NEW_DATA_PATH = os.getenv("NEW_DATA_PATH", "portman_ML/data/new_ports_multi.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "portman_ML/models/")

# === Domain-specific thresholds ===
LOW_SNR_THRESHOLD = float(os.getenv("LOW_SNR_THRESHOLD", "20"))

# === Feature settings ===
DROP_COLUMNS = ["oper_status", "downstream_snr", "line_profile"]
TARGET_COLUMN = "low_snr_risk"
