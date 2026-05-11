# ============================================================
# scaler_logic.py
#
# ONLY THE NEW OPTIMAL SCALING LOGIC
# (Communicates with model + metrics + AWS files)
# ============================================================

import numpy as np

from config import (
    QOS_MAX,
    K_MIN,
    K_MAX
)

from aws_manager import (
    launch_instance,
    terminate_instance
)

from lb_manager import (
    update_load_balancer
)

from worker_tracker import workers


# ============================================================
# ALGORITHM 1:
# Selecting Optimal Number of VMs
# ============================================================

def select_optimal_vm_count(

    model,
    scaler,

    current_metrics,

    current_workers
):

    """
    current_metrics:
    [cpu, memory, requests]

    current_workers:
    current active VM count
    """

    k_op = None

    cpu = current_metrics[0]
    mem = current_metrics[1]
    req = current_metrics[2]

    # ========================================================
    # Try every scaling possibility
    # ========================================================

    for k in range(K_MIN, K_MAX + 1):

        new_workers = current_workers + k

        # Invalid worker count
        if new_workers <= 0:
            continue

        # ====================================================
        # Estimate future metrics
        # ====================================================

        est_cpu = (
            cpu * current_workers
        ) / new_workers

        est_mem = (
            mem * current_workers
        ) / new_workers

        est_req = (
            req * current_workers
        ) / new_workers

        # ====================================================
        # Build feature vector
        # ====================================================

        X = np.array([[
            est_cpu,
            est_mem,
            est_req,
            new_workers
        ]])

        # ====================================================
        # Normalize features
        # ====================================================

        X = scaler.transform(X)

        # ====================================================
        # Predict response time
        # ====================================================

        pred_rt = model.predict(
            X,
            verbose=0
        )[0][0]

        print(
            f"k={k} | "
            f"workers={new_workers} | "
            f"PredRT={pred_rt:.2f} ms"
        )

        # ====================================================
        # QoS satisfied
        # ====================================================

        if pred_rt < QOS_MAX:

            k_op = k

            break

    # ========================================================
    # No QoS solution found
    # ========================================================

    if k_op is None:

        k_op = K_MAX

    return k_op


# ============================================================
# APPLY SCALING DECISION
# ============================================================

def apply_scaling(k_op):

    # ========================================================
    # SCALE OUT
    # ========================================================

    if k_op > 0:

        print(
            f"\nScaling OUT by {k_op} VMs"
        )

        for _ in range(k_op):

            node = launch_instance()

            workers.append(node)

    # ========================================================
    # SCALE IN
    # ========================================================

    elif k_op < 0:

        print(
            f"\nScaling IN by {abs(k_op)} VMs"
        )

        for _ in range(abs(k_op)):

            if len(workers) <= 1:
                break

            victim = workers.pop()

            terminate_instance(
                victim["id"]
            )

    # ========================================================
    # UPDATE LOAD BALANCER
    # ========================================================

    worker_ips = [
        w["ip"]
        for w in workers
    ]

    update_load_balancer(
        worker_ips
    )

    print(
        "\nUpdated Cluster Size:",
        len(workers)
    )
