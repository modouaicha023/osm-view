# api.py
from flask import Flask, jsonify, request, send_file
import json
import os
from optimizer import RouteOptimizer
from visualizer import RouteVisualizer
import pandas as pd

app = Flask(__name__)

# Configuration
CHATEAU_COORDS = (48.45038746219548, -2.0447748346342434)
MAX_DISTANCE_KM = 15
GEOJSON_FILE = 'dinan_osm_data.geojson'

# Initialiser l'optimiseur et le visualiseur
optimizer = RouteOptimizer(CHATEAU_COORDS, MAX_DISTANCE_KM)
visualizer = RouteVisualizer(CHATEAU_COORDS, MAX_DISTANCE_KM)

# Charger les données OSM


def load_points():
    if os.path.exists('points_cache.json'):
        with open('points_cache.json', 'r') as f:
            return json.load(f)
    else:
        from script import load_osm_data
        points = load_osm_data(GEOJSON_FILE, CHATEAU_COORDS, MAX_DISTANCE_KM)
        with open('points_cache.json', 'w') as f:
            json.dump(points, f)
        return points

# Routes API


@app.route('/api/points', methods=['GET'])
def get_points():
    points = load_points()
    return jsonify(points)


@app.route('/api/optimize', methods=['POST'])
def optimize_routes():
    config = request.json or {}

    num_drivers = config.get('num_drivers', 3)
    capacity = config.get('capacity_per_driver', 8)
    max_distance = config.get('max_distance_km', 15)

    # Mettre à jour l'optimiseur avec les nouvelles configurations
    optimizer.num_drivers = num_drivers
    optimizer.capacity_per_driver = capacity
    optimizer.max_distance_km = max_distance

    # Charger les points
    points = load_points()

    # Optimiser les itinéraires
    manager, routing, solution, data = optimizer.solve(points)

    if not solution:
        return jsonify({'error': 'No solution found'}), 400

    # Générer les itinéraires
    routes = visualizer.extract_routes(manager, routing, solution, data)

    # Sauvegarder les routes
    route_df = pd.DataFrame(routes['routes_details'])
    route_df.to_csv("routes_optimisees.csv", index=False)

    # Générer la carte
    map_file = "static/map.html"
    visualizer.create_map(points, routes['routes']).save(map_file)

    return jsonify({
        'routes': routes['routes'],
        'total_distance': routes['total_distance'],
        'total_passengers': routes['total_passengers'],
        'map_url': '/static/map.html'
    })


@app.route('/api/map', methods=['GET'])
def get_map():
    return send_file('static/map.html')


@app.route('/api/driver/<int:driver_id>', methods=['GET'])
def get_driver_route(driver_id):
    # Lire les routes optimisées
    if os.path.exists('routes_optimisees.csv'):
        routes_df = pd.read_csv('routes_optimisees.csv')
        driver_routes = routes_df[routes_df['driver_id']
                                  == driver_id].to_dict('records')
        return jsonify(driver_routes)
    else:
        return jsonify({'error': 'No routes found'}), 404


if __name__ == '__main__':
    # Créer le dossier static s'il n'existe pas
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
