# neural_network_scaler.py

import time
import requests
import numpy as np
import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.preprocessing import StandardScaler

# =========================================================
# CONFIG
# =========================================================

RT_SERVER = "http://3.223.3.55:9200/rt_stats"

WORKERS = [
    "172.31.71.219"
]

TARGET_RT_HIGH = 800
TARGET_RT_LOW = 300

# =========================================================
# METRIC COLLECTION
# =========================================================

def get_worker_metrics(worker_ip):

    try:

        res = requests.get(
            f"http://{worker_ip}:9100/metrics",
            timeout=3
        )

        data = res.json()

        return [
            float(data["cpu"]),
            float(data["memory"]),
            float(data["requests"])
        ]

    except:

        return None


def get_response_time():

    try:

        res = requests.get(
            RT_SERVER,
            timeout=5
        )

        return float(
            res.json()["response_time_ms"]
        )

    except:

        return None


# =========================================================
# DATASET GENERATION
# =========================================================

X = []
y = []

print("Collecting training data...")

for _ in range(100):

    total_cpu = 0
    total_mem = 0
    total_req = 0

    count = 0

    for ip in WORKERS:

        metrics = get_worker_metrics(ip)

        if metrics:

            total_cpu += metrics[0]
            total_mem += metrics[1]
            total_req += metrics[2]

            count += 1

    if count == 0:

        continue

    avg_cpu = total_cpu / count
    avg_mem = total_mem / count
    avg_req = total_req / count

    rt = get_response_time()

    if rt is None:

        continue

    X.append([
        avg_cpu,
        avg_mem,
        avg_req,
        count
    ])

    y.append(rt)

    print(
        f"Collected -> CPU:{avg_cpu:.2f} "
        f"MEM:{avg_mem:.2f} "
        f"REQ:{avg_req:.2f} "
        f"RT:{rt:.2f}"
    )

    time.sleep(5)

X = np.array(X)
y = np.array(y)

# =========================================================
# FEATURE SCALING
# =========================================================

scaler = StandardScaler()

X = scaler.fit_transform(X)

# =========================================================
# TENSORFLOW NEURAL NETWORK
# =========================================================

model = Sequential([

    Dense(
        64,
        activation='relu',
        input_shape=(4,)
    ),

    Dense(
        32,
        activation='relu'
    ),

    Dense(
        16,
        activation='relu'
    ),

    Dense(
        1
    )
])

model.compile(

    optimizer='adam',

    loss='mse',

    metrics=['mae']
)

# =========================================================
# TRAIN MODEL
# =========================================================

print("\nTraining Neural Network...\n")

model.fit(

    X,
    y,

    epochs=200,

    batch_size=8,

    verbose=1
)

# =========================================================
# LIVE PREDICTION + SCALING DECISION
# =========================================================

print("\nStarting intelligent autoscaler...\n")

while True:

    total_cpu = 0
    total_mem = 0
    total_req = 0

    count = 0

    for ip in WORKERS:

        metrics = get_worker_metrics(ip)

        if metrics:

            total_cpu += metrics[0]
            total_mem += metrics[1]
            total_req += metrics[2]

            count += 1

    if count == 0:

        print("No workers available")

        time.sleep(10)

        continue

    avg_cpu = total_cpu / count
    avg_mem = total_mem / count
    avg_req = total_req / count

    features = np.array([[
        avg_cpu,
        avg_mem,
        avg_req,
        count
    ]])

    features = scaler.transform(features)

    pred_rt = model.predict(
        features,
        verbose=0
    )[0][0]

    print(
        f"\nPredicted RT = {pred_rt:.2f} ms"
    )

    # =====================================================
    # SCALING DECISION
    # =====================================================

    if pred_rt > TARGET_RT_HIGH:

        print("Decision: SCALE OUT")

        # launch_instance()

    elif pred_rt < TARGET_RT_LOW:

        print("Decision: SCALE IN")

        # terminate_instance()

    else:

        print("Decision: STABLE")

    time.sleep(20)