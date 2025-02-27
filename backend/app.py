from fastapi import FastAPI
from osm_loader import load_osm_data
from vrp_solver import solve_vrp
import folium
import json

app = FastAPI()

CHATEAU_COORDS = (48.450387, -2.044774)
MAX_DISTANCE_KM = 15


@app.get("/optimisation")
def optimisation():
    geojson_file = "data/dinan_osm_data.geojson"
    points = load_osm_data(geojson_file, CHATEAU_COORDS, MAX_DISTANCE_KM)

    if not points:
        return {"message": "Aucun point trouvé dans la zone spécifiée."}

    data = solve_vrp(CHATEAU_COORDS, points)

    return {"routes": data}


@app.get("/carte")
def generate_map():
    geojson_file = "data/dinan_osm_data.geojson"
    points = load_osm_data(geojson_file, CHATEAU_COORDS, MAX_DISTANCE_KM)

    if not points:
        return {"message": "Aucun point trouvé."}

    map_viz = folium.Map(location=CHATEAU_COORDS, zoom_start=13)

    folium.Marker(location=CHATEAU_COORDS, popup="Château de Dinan",
                  icon=folium.Icon(color="red")).add_to(map_viz)

    for point in points:
        folium.Marker(
            location=[point["lat"], point["lon"]],
            popup=f"{point['name']} ({point['passengers']} passagers)",
            icon=folium.Icon(color="blue")
        ).add_to(map_viz)

    map_viz.save("map.html")
    return {"message": "Carte générée avec succès.", "file": "map.html"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
