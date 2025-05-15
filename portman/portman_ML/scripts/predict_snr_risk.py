import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from portman.predict import predict_from_csv
from portman.config import MODEL_PATH, NEW_DATA_PATH

drop_cols = ["oper_status", "downstream_snr"]
preds, df = predict_from_csv(MODEL_PATH, NEW_DATA_PATH, drop_columns=drop_cols)

for i, p in enumerate(preds):
    status = "⚠️ AT RISK" if p else "✅ OK"
    print(f"Port {i+1}: {status}")
