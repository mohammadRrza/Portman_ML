

from celery import shared_task
import subprocess

@shared_task
def train_model_task():
    subprocess.run(["python", "manage.py", "train_model"])

@shared_task
def predict_model_task():
    subprocess.run(["python", "manage.py", "predict_model"])
