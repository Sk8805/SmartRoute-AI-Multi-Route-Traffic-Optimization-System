// 🔑 MapTiler API Key
const MAPTILER_KEY = "aTKpPp8VHRvaKuMqVakT";

// Backend URL
const BACKEND_URL = "http://127.0.0.1:5000";

let map;
let routeLayers = [];
let routeSources = [];
let startMarker, endMarker;
let activeRouteId = null;

// ---------------- INITIALIZE MAP ----------------
document.addEventListener("DOMContentLoaded", () => {
  map = new maplibregl.Map({
    container: "map",
    style: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_KEY}`,
    center: [88.3639, 22.5726],
    zoom: 11,
  });

  map.addControl(new maplibregl.NavigationControl());

  // ---------------- SWAP BUTTON ----------------
  document.getElementById("swap").addEventListener("click", () => {
    let startInput = document.getElementById("start");
    let endInput = document.getElementById("end");
    let a = startInput.value;
    let b = endInput.value;
    startInput.value = b;
    endInput.value = a;
  });

  // ---------------- FIND ROUTES BUTTON ----------------
  document.getElementById("findRoutes").addEventListener("click", async () => {
    let startInput = document.getElementById("start");
    let endInput = document.getElementById("end");
    let startPlace = startInput.value.trim();
    let endPlace = endInput.value.trim();

    if (!startPlace || !endPlace) {
      alert("Please enter both starting point and destination");
      return;
    }

    try {
      let routesDiv = document.querySelector(".routes");
      routesDiv.innerHTML = "<h3>Finding Routes...</h3><p>Please wait...</p>";

      let startCoords = await geocode(startPlace);
      let endCoords = await geocode(endPlace);

      if (!startCoords || !endCoords) {
        alert("Location not found");
        routesDiv.innerHTML = "<h3>Available Routes</h3>";
        return;
      }

      showMarkers(startCoords, endCoords);

      await getRoutes(startCoords, endCoords);
    } catch (error) {
      console.error("Error finding routes:", error);
      alert("Error finding routes");
    }
  });
});

// ---------------- GEOCODING ----------------
async function geocode(place) {
  try {
    let url = `${BACKEND_URL}/geocode?place=${encodeURIComponent(place)}`;
    let response = await fetch(url);
    let data = await response.json();

    if (data.error) return null;

    return [data.longitude, data.latitude];
  } catch {
    return null;
  }
}

// ---------------- MARKERS ----------------
function showMarkers(start, end) {
  if (startMarker) startMarker.remove();
  if (endMarker) endMarker.remove();

  startMarker = new maplibregl.Marker({ color: "green" })
    .setLngLat(start)
    .addTo(map);

  endMarker = new maplibregl.Marker({ color: "red" })
    .setLngLat(end)
    .addTo(map);

  map.fitBounds([start, end], { padding: 80 });
}

// ---------------- GET ROUTES ----------------
async function getRoutes(start, end) {
  try {
    routeLayers.forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    routeSources.forEach((id) => {
      if (map.getSource(id)) map.removeSource(id);
    });

    routeLayers = [];
    routeSources = [];

    let routesDiv = document.querySelector(".routes");
    routesDiv.innerHTML = "<h3>Available Routes</h3>";

    let url = `${BACKEND_URL}/route?start_lat=${start[1]}&start_lng=${start[0]}&end_lat=${end[1]}&end_lng=${end[0]}`;

    let response = await fetch(url);
    let data = await response.json();

    if (data.error) {
      alert("No routes found");
      return;
    }

    let routes = data.routes;

    routes.forEach((route, index) => {
      let id = "route" + index;

      let color =
        index === 0 ? "#4caf50" :
        index === 1 ? "#ff9800" :
        index === 2 ? "#2196f3" : "#9e9e9e";

      map.addSource(id, {
        type: "geojson",
        data: {
          type: "Feature",
          geometry: route.geometry,
        },
      });

      map.addLayer({
        id: id,
        type: "line",
        source: id,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": color,
          "line-width": index === 0 ? 6 : 0,
          "line-opacity": index === 0 ? 1 : 0.7,
        },
      });

      routeLayers.push(id);
      routeSources.push(id);

      addRouteCard(route, index, id, color);
    });

    activeRouteId = "route0";
  } catch (error) {
    console.error(error);
    alert("Error fetching routes");
  }
}

// ---------------- ROUTE CARDS ----------------
function addRouteCard(route, index, layerId, color) {
  let routesDiv = document.querySelector(".routes");

  let card = document.createElement("div");
  card.className = "route-card" + (index === 0 ? " best active" : "");

  let trafficLevel = route.traffic;

  let trafficColor =
    trafficLevel === "Low"
      ? "#4caf50"
      : trafficLevel === "Medium"
      ? "#ff9800"
      : "#f44336";

  card.innerHTML = `
    <div class="route-header">
      <span class="rank-badge ${
        index === 0 ? "best-badge" : ""
      }">${index === 0 ? "RECOMMENDED" : "Route " + (index + 1)}</span>
      <div class="route-color-indicator" style="background:${color}"></div>
    </div>

    <div class="route-details">
      <div>Time: ${route.duration_min} mins</div>
      <div>Distance: ${route.distance_km} km</div>
      <div style="color:${trafficColor}; font-weight:bold;">
        Traffic: ${trafficLevel}
      </div>
      <div>Speed: ${route.avg_speed} km/h</div>
    </div>

    ${
      index === 0
        ? `<div class="best-route-reason">
            ✓ Selected using ML (least traffic)
          </div>`
        : ""
    }
  `;

  card.addEventListener("click", () => {
    document.querySelectorAll(".route-card").forEach((c) =>
      c.classList.remove("active")
    );

    card.classList.add("active");

    routeLayers.forEach((id) => {
      if (map.getLayer(id)) map.setPaintProperty(id, "line-width", 0);
    });

    map.setPaintProperty(layerId, "line-width", 6);
    activeRouteId = layerId;
  });

  routesDiv.appendChild(card);
}