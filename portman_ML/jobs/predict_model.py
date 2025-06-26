# portman_ml/jobs/predict_model.py

import os
import pandas as pd
import joblib
from django.core.mail import EmailMessage
from django.conf import settings
from dj_bridge import DSLAMPort
from portman.config import MODEL_PATH
from dj_bridge import LineProfilePrediction
from portman.portman_ML.utils.mail import Mail

def run():
    print("🔍 Running prediction job...")

    bundle = joblib.load(os.path.join(MODEL_PATH, "profile_recommender_xgb.pkl"))
    model = bundle["model"]
    label_encoder = bundle["label_encoder"]

    queryset = DSLAMPort.objects.all().values()
    df = pd.DataFrame(list(queryset)).dropna(subset=["downstream_snr", "line_profile"])

    X = df.drop(columns=["downstream_snr", "line_profile", "oper_status"], errors="ignore")
    preds = model.predict(X)

    df["predicted_profile"] = label_encoder.inverse_transform(preds)

    df[["id", "predicted_profile"]].to_csv("predicted_profiles.csv", index=False)
    send_prediction_results()
    print("✅ Predictions saved to predicted_profiles.csv")


def save_predictions_to_db(X, decoded_preds):
    for i, pred in enumerate(decoded_preds):
        LineProfilePrediction.objects.create(
            port_id=X.index[i],
            predicted_profile=pred
        )




def send_prediction_results():
    mail = Mail()
    mail.from_addr = "oss-problems@pishgaman.net"
    mail.to_addr = "ml-results@pishgaman.net"
    mail.msg_subject = "📊 ML Line Profile Predictions"
    mail.msg_body = "Please find the attached prediction results."
    mail.attachment = "predicted_profiles.csv"

    Mail.Send_Mail_With_Attachment(mail)