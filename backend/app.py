from fastapi import FastAPI, HTTPException
from osm_loader import load_osm_data
from vrp_solver import solve_vrp
import folium
import json

app = FastAPI()

CHATEAU_COORDS = (48.450387, -2.044774)
MAX_DISTANCE_KM = 15


@app.get("/optimisation")
def optimisation():
    try:
        geojson_file = "data/dinan_osm_data.geojson"
        points = load_osm_data(geojson_file, CHATEAU_COORDS, MAX_DISTANCE_KM)

        if not points:
            raise HTTPException(status_code=404, detail="Aucun point trouvé.")

        data = solve_vrp(CHATEAU_COORDS, points)
        return {"routes": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/routes/{driver_id}")
def get_route(driver_id: int):
    """ Récupère un trajet spécifique """
    try:
        geojson_file = "data/dinan_osm_data.geojson"
        points = load_osm_data(geojson_file, CHATEAU_COORDS, MAX_DISTANCE_KM)

        if not points:
            raise HTTPException(status_code=404, detail="Aucun point trouvé.")

        data = solve_vrp(CHATEAU_COORDS, points)

        if driver_id >= len(data):
            raise HTTPException(
                status_code=404, detail="Aucune route pour ce chauffeur.")

        return {"driver_id": driver_id, "route": data[driver_id]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
