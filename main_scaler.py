 
import time
import requests
from aws_manager import launch_instance, terminate_instance
from scaler_logic import decide
from lb_updater import update_lb
from ml_model import train_model, predict_workers
from config import *
import pandas as pd
import sys

workers = []

def get_rt():
    try:
        res = requests.get(RT_SERVER, timeout=3)
        return res.json()["response_time_ms"]
    except:
        return 1000


THRESHOLD = 6  # ms
MIN_WORKERS = 1
MAX_WORKERS = 6        
def live():
    workers = []

    while True:
        rt = get_rt()

        current_workers = len(workers)

        # 🎯 DECISION LOGIC
        decision = decide(rt, current_workers, MAX_WORKERS, MIN_WORKERS)

        print(f"RT={rt:.2f} ms → {decision}")             
          # 🚀 SCALE OUT
        if decision == "scale_out":
            instance_id, ip = launch_instance()
            workers.append((instance_id, ip))

        # 🔽 SCALE IN
        elif decision == "scale_in":
            instance_id, ip = workers.pop()
            terminate_instance(instance_id)

        # 🔥 UPDATE LOAD BALANCER
        worker_ips = [w[1] for w in workers]
        update_lb(worker_ips)

        time.sleep(10)
def perturb():
    workers = []
    data = []

    for w in range(1, 6):

        while len(workers) < w:
            instance_id, ip = launch_instance()
            workers.append((instance_id, ip))

        while len(workers) > w:
            instance_id, ip = workers.pop()
            terminate_instance(instance_id)

        update_lb([x[1] for x in workers])
        time.sleep(20)

        rt = get_rt()

        data.append({
            "response_time_ms": rt,
            "workers": w
        })

        print(f"Collected → workers={w}, RT={rt}")

    pd.DataFrame(data).to_csv("training_data.csv", index=False)
def live_ml():
    workers = []

    while True:
        rt = get_rt()

        target = predict_workers(rt)

        print(f"RT={rt:.2f} → ML predicts {target} workers")

        while len(workers) < target:
            instance_id, ip = launch_instance()
            workers.append((instance_id, ip))

        while len(workers) > target:
            instance_id, ip = workers.pop()
            terminate_instance(instance_id)

        update_lb([x[1] for x in workers])

        time.sleep(10)
if __name__ == "__main__":
    mode = sys.argv[1]

    if mode == "perturb":
        perturb()

    elif mode == "train":
        train_model()

    elif mode == "live_ml":
        live_ml()

    else:
        print("Invalid mode")
