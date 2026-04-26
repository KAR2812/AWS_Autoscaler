import pandas as pd
import random

data = []

print("Simulating server load and generating data...")

# Generate 200 rows of fake historical data
for _ in range(200):
    # Randomly pick a target number of workers (1 to 6)
    target_workers = random.randint(1, 6)
    
    # Simulate the response time that would require this many workers.
    # We use a base of 150ms per worker, plus some random "network jitter" (-40ms to +40ms)
    base_rt = target_workers * 150
    jitter = random.uniform(-40, 40)
    
    final_rt = base_rt + jitter
    
    data.append({
        "response_time_ms": round(final_rt, 2),
        "workers": target_workers
    })

# Convert the list to a Pandas DataFrame and save it as a CSV
df = pd.DataFrame(data)
df.to_csv("training_data.csv", index=False)

print("✅ Successfully created 'training_data.csv' with 200 data points!")
print("Sample of the data:")
print(df.head())