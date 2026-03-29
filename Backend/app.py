from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import joblib
from datetime import datetime

# ---------------- LOAD MODEL ----------------
model = joblib.load("model.pkl")
labels = ["Low", "Medium", "High"]

app = Flask(__name__)
CORS(app)

# ---------------- HOME TEST ----------------
@app.route("/")
def home():
    return "Flask backend is running successfully 🔥"


# ---------------- ML PREDICTION FUNCTION ----------------
def predict_traffic(avg_speed, distance_km, duration_min):
    now = datetime.now()

    
    future_hour = (now.hour + 1) % 24

    features = [[
        distance_km,
        duration_min,
        avg_speed,
        future_hour,
        now.weekday(),
        150,   
        1      
    ]]

    pred = model.predict(features)[0]
    return labels[pred]


# ---------------- GEOCODING ----------------
@app.route("/geocode")
def geocode():
    place = request.args.get("place")

    if not place:
        return jsonify({"error": "Place name is required"}), 400

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "multi-route-optimizer-project"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if len(data) == 0:
            return jsonify({"error": "Location not found"}), 404

        return jsonify({
            "place": place,
            "latitude": float(data[0]["lat"]),
            "longitude": float(data[0]["lon"])
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Geocoding service error: {str(e)}"}), 500


# ---------------- ROUTE + ML TRAFFIC ----------------
@app.route("/route")
def route():
    start_lat = request.args.get("start_lat")
    start_lng = request.args.get("start_lng")
    end_lat = request.args.get("end_lat")
    end_lng = request.args.get("end_lng")

    if not all([start_lat, start_lng, end_lat, end_lng]):
        return jsonify({"error": "Start and end coordinates are required"}), 400

    # OSRM API
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"

    params = {
        "alternatives": "true",
        "geometries": "geojson",
        "overview": "full",
        "steps": "true"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "routes" not in data or len(data["routes"]) == 0:
            return jsonify({"error": "No routes found"}), 404

        routes = data["routes"]
        result = []

        for idx, route in enumerate(routes):
            distance_km = round(route["distance"] / 1000, 2)
            duration_min = round(route["duration"] / 60, 2)

            avg_speed = round(
                (distance_km / (duration_min / 60)), 1
            ) if duration_min > 0 else 0

            # 🔥 ML Prediction
            traffic_label = predict_traffic(avg_speed, distance_km, duration_min)

            score_map = {
                "Low": 1,
                "Medium": 2,
                "High": 3
            }

            traffic_score = score_map[traffic_label]

            # Final ranking score (ML weighted more)
            overall_score = (
                duration_min * 2 +
                distance_km * 0.5 +
                traffic_score * 15
            )

            result.append({
                "rank": idx + 1,
                "distance_km": distance_km,
                "duration_min": duration_min,
                "avg_speed": avg_speed,
                "traffic": traffic_label,
                "traffic_score": traffic_score,
                "overall_score": overall_score,
                "geometry": route["geometry"]
            })

        # Sort best route first
        result.sort(key=lambda r: r["overall_score"])

        for idx, r in enumerate(result):
            r["rank"] = idx + 1

        return jsonify({
            "total_routes": len(result),
            "routes": result,
            "recommendation": {
                "best_route_index": 0,
                "reason": "Best route selected using ML traffic prediction",
                "time_saved": round(
                    result[1]["duration_min"] - result[0]["duration_min"], 1
                ) if len(result) > 1 else 0
            }
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Routing service error: {str(e)}"}), 500


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
