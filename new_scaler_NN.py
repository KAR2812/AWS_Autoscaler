# ============================================================
# scaler_logic.py
#
# ONLY THE NEW OPTIMAL SCALING LOGIC
# (Communicates with model + metrics + AWS files)
# ============================================================

# Algorithm 1: Selecting the Optimal Number of VMs to Scale (k_op)

def select_optimal_vms(QoS_max, K_min, K_max, M, w, coefficients, f_NN):
    """
    QoS_max   : Upper limit of QoS (RT)
    K_min     : Lowest delta VM (e.g., -7)
    K_max     : Highest delta VM (e.g., +7)
    M         : Vector of metrics (e.g., CPU usage)
    w         : Actual number of VMs
    coefficients : List of tuples (c_i0, c_i1, c_i2)
    f_NN      : Neural network prediction function
    """

    # Initialize k_op as None
    k_op = None

    # Iterate through possible VM scaling values
    for k in range(K_min, K_max + 1):

        # Empty list for transformed metrics
        M_prime = []

        # Update each metric
        for i in range(len(M)):

            m_i = M[i]
            c_i0, c_i1, c_i2 = coefficients[i]

            m_i_prime = (
                c_i0
                + c_i1 * m_i * (w / (w + k))
                + c_i2 * m_i * (k / (w + k))
            )

            # Append updated metric
            M_prime.append(m_i_prime)

        # Predict response time using neural network
        RT_est = f_NN(M_prime)

        # Check QoS constraint
        if RT_est < QoS_max:
            k_op = k
            break

    # If no valid scaling found
    if k_op is None:
        k_op = K_max

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






# =========================================================
# LIVE AUTOSCALER LOOP
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

    print(
        f"\nCurrent State → CPU:{avg_cpu:.2f} "
        f"MEM:{avg_mem:.2f} "
        f"REQ:{avg_req:.2f} "
        f"Workers:{count}"
    )

    # =====================================================
    # SELECT OPTIMAL SCALING ACTION
    # =====================================================

    k_op = select_optimal_k(
        avg_cpu,
        avg_mem,
        avg_req,
        count
    )

    print(f"\nOptimal scaling decision k_op = {k_op}")

    # =====================================================
    # APPLY SCALING
    # =====================================================

    if k_op > 0:

        print(f"Scaling OUT by {k_op}")

        for _ in range(k_op):
            print("Launching instance...")
            # launch_instance()

    elif k_op < 0:

        print(f"Scaling IN by {abs(k_op)}")

        for _ in range(abs(k_op)):
            print("Terminating instance...")
            # terminate_instance()

    else:

        print("System is STABLE")

    time.sleep(20)





