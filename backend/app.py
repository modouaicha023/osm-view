import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from osm_loader import load_osm_data
from vrp_solver import solve_vrp, simple_route_distribution
import logging
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHATEAU_COORDS = (48.450387, -2.044774)
MAX_DISTANCE_KM = 15

GEOJSON_FILE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'dinan_osm_data.geojson')


@app.get("/optimisation")
def optimisation():
    try:
        geojson_file = GEOJSON_FILE
        points = load_osm_data(geojson_file, CHATEAU_COORDS, MAX_DISTANCE_KM)

        if not points:
            raise HTTPException(status_code=404, detail="Aucun point trouvé.")

        try:
            data = solve_vrp(CHATEAU_COORDS, points)
        except Exception as e:
            logging.warning(
                f"VRP solver failed: {e}. Using simple route distribution.")
            data = simple_route_distribution(CHATEAU_COORDS, points)

        return {"routes": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/routes/{driver_id}")
def get_route(driver_id: int):
    """ Récupère un trajet spécifique """
    try:
        points = load_osm_data(GEOJSON_FILE, CHATEAU_COORDS, MAX_DISTANCE_KM)

        if not points:
            raise HTTPException(status_code=404, detail="Aucun point trouvé.")

        data = solve_vrp(CHATEAU_COORDS, points)

        if driver_id >= len(data):
            raise HTTPException(
                status_code=404, detail="Aucune route pour ce chauffeur.")

        return {"driver_id": driver_id, "route": data[driver_id]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize_route")
async def optimize_custom_route(request: Request):
    data = await request.json()
    start_point = data.get('start_point')
    delivery_points = data.get('delivery_points')
    vehicle_count = data.get('vehicle_count', 2)
    max_distance = data.get('max_distance', 15)

    points = [
        {
            'lat': point['latitude'],
            'lon': point['longitude'],
            'passengers': random.randint(1, 3),
            'name': 'Delivery Point'
        }
        for point in delivery_points
    ]

    routes = solve_vrp(
        (start_point['latitude'], start_point['longitude']),
        points,
        max_points=30
    )

    return {"routes": routes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
