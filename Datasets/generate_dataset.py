import pandas as pd
import random

rows = []

for _ in range(20000):
    distance = random.uniform(50, 500)
    avg_speed = random.uniform(20, 100)
    time = (distance / avg_speed) * 60

    hour = random.randint(0, 23)
    day = random.randint(0, 6)
    vehicle_count = random.randint(50, 300)
    road_type = random.randint(0, 2)

    # REALISTIC TRAFFIC LOGIC
    if hour in range(8, 11) or hour in range(17, 21):
        if avg_speed < 40 or vehicle_count > 200:
            traffic = "High"
        elif avg_speed < 60:
            traffic = "Medium"
        else:
            traffic = "Low"
    else:
        if avg_speed < 35:
            traffic = "Medium"
        else:
            traffic = "Low"

    rows.append([
        distance, time, avg_speed, hour, day,
        vehicle_count, road_type, traffic
    ])

df = pd.DataFrame(rows, columns=[
    "distance", "time", "avg_speed", "hour", "day",
    "vehicle_count", "road_type", "traffic"
])

df.to_csv("data.csv", index=False)

print("✅ Dataset created!")