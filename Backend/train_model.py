import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix

import joblib

# -----------------------------
# 1. LOAD DATA
# -----------------------------
import os

file_path = os.path.join(os.path.dirname(__file__), "../india_traffic_no_weather_best_route.csv")
data = pd.read_csv(file_path)

# Shuffle data
data = data.sample(frac=1, random_state=42).reset_index(drop=True)

# -----------------------------
# 2. ADD FEATURE NOISE (REALISTIC)
# -----------------------------
data["avg_speed"] += np.random.normal(0, 5, len(data))
data["vehicle_count"] += np.random.normal(0, 20, len(data))

# Clip to valid range
data["avg_speed"] = data["avg_speed"].clip(10, 120)
data["vehicle_count"] = data["vehicle_count"].clip(10, 500)

# -----------------------------
# 3. ADD LABEL NOISE (IMPORTANT)
# -----------------------------
labels = ["Low", "Medium", "High"]

noise_idx = np.random.choice(
    data.index,
    size=int(0.05 * len(data)),
    replace=False
)

for i in noise_idx:
    data.at[i, "traffic"] = np.random.choice(labels)

# -----------------------------
# 4. ENCODE TARGET (AFTER NOISE)
# -----------------------------
le = LabelEncoder()
data["traffic"] = le.fit_transform(data["traffic"])

# -----------------------------
# 5. FEATURES & TARGET
# -----------------------------
X = data[[
    "distance", "time", "avg_speed",
    "hour", "day", "vehicle_count", "road_type"
]]

y = data["traffic"]

# -----------------------------
# 6. TRAIN TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.3,
    random_state=42
)

# -----------------------------
# 7. MODEL (ANTI-OVERFITTING)
# -----------------------------
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=8,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42
)

# Train
model.fit(X_train, y_train)

# -----------------------------
# 8. EVALUATION
# -----------------------------
y_pred = model.predict(X_test)

print("✅ Accuracy:", accuracy_score(y_test, y_pred))
print("📊 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# -----------------------------
# 9. SAVE MODEL
# -----------------------------
joblib.dump(model, "model.pkl")

print("💾 Model saved as model.pkl")
