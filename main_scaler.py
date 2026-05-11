# =========================================================
# MAIN SCALER (LINEAR REGRESSION BASED)
# =========================================================

import time
import requests
import numpy as np
import pickle

from aws_manager import launch_instance, terminate_instance
from lb_updater import update_lb
from config import RT_SERVER

# =========================================================
# LOAD TRAINED MODEL
# =========================================================

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

print("Loaded Linear Regression model")

# =========================================================
# GLOBAL STATE
# =========================================================

workers = []  # list of (instance_id, ip)

TARGET_RT = 6   # ms target (you mentioned ~6ms)

# =========================================================
# GET RESPONSE TIME
# =========================================================

def get_response_time():

    try:
        res = requests.get(RT_SERVER, timeout=5)
        return float(res.json()["response_time_ms"])

    except:
        return None

# =========================================================
# PREDICT REQUIRED WORKERS
# =========================================================

def predict_workers(rt):

    X = np.array([[rt]])

    pred = model.predict(X)[0]

    # round and clamp
    pred = int(round(pred))

    pred = max(1, min(pred, 6))  # keep between 1–6

    return pred

# =========================================================
# SCALING LOGIC
# =========================================================

def live():

    global workers

    print("\nStarting Linear Regression Autoscaler...\n")

    while True:

        rt = get_response_time()

        if rt is None:

            print("Failed to fetch RT")
            time.sleep(5)
            continue

        current_workers = len(workers)

        predicted_workers = predict_workers(rt)

        print(
            f"RT={rt:.2f} ms | "
            f"Current={current_workers} | "
            f"Predicted={predicted_workers}"
        )

        # =====================================================
        # DECISION
        # =====================================================

        if predicted_workers > current_workers:

            scale = predicted_workers - current_workers

            print(f"Scaling OUT by {scale}")

            for _ in range(scale):

                instance_id, ip = launch_instance()

                workers.append((instance_id, ip))

                print(f"Launched: {instance_id} | {ip}")

        elif predicted_workers < current_workers:

            scale = current_workers - predicted_workers

            print(f"Scaling IN by {scale}")

            for _ in range(scale):

                instance_id, ip = workers.pop()

                terminate_instance(instance_id)

                print(f"Terminated: {instance_id}")

        else:

            print("System is STABLE")

        # =====================================================
        # UPDATE LOAD BALANCER
        # =====================================================

        worker_ips = [w[1] for w in workers]

        update_lb(worker_ips)

        time.sleep(10)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    live()
