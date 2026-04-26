# ml_model.py

import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression

MODEL_FILE = "model.pkl"
TRAIN_FILE = "training_data.csv"


def train_model():
    df = pd.read_csv(TRAIN_FILE)

    X = df[["response_time_ms"]]
    y = df["workers"]

    model = LinearRegression()
    model.fit(X, y)

    joblib.dump(model, MODEL_FILE)
    print("✅ Model trained")


def predict_workers(rt):
    model = joblib.load(MODEL_FILE)

    pred = model.predict([[rt]])[0]

    # safety clamp
    pred = int(round(pred))
    pred = max(1, min(pred, 6))

    return pred