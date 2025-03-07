from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
import json
import os
from optimizer import RouteOptimizer
from visualizer import RouteVisualizer
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

CHATEAU_COORDS = (48.45038746219548, -2.0447748346342434)
MAX_DISTANCE_KM = 15
GEOJSON_FILE = 'dinan_osm_data.geojson'

optimizer = RouteOptimizer(CHATEAU_COORDS, MAX_DISTANCE_KM)
visualizer = RouteVisualizer(CHATEAU_COORDS, MAX_DISTANCE_KM)


def validate_time_window(time_str):
    """Valide si une heure est dans la fenêtre 8h-12h ou 14h-16h"""
    try:
        time = datetime.strptime(time_str, "%H:%M").time()
        morning_start = datetime.strptime("08:00", "%H:%M").time()
        morning_end = datetime.strptime("12:00", "%H:%M").time()
        afternoon_start = datetime.strptime("14:00", "%H:%M").time()
        afternoon_end = datetime.strptime("16:00", "%H:%M").time()

        return (morning_start <= time <= morning_end) or (afternoon_start <= time <= afternoon_end)
    except ValueError:
        return False


def load_points():
    """Charge et valide les points depuis le cache ou OSM"""
    try:
        if os.path.exists('points_cache.json'):
            with open('points_cache.json', 'r') as f:
                points = json.load(f)
        else:
            from script import load_osm_data
            points = load_osm_data(
                GEOJSON_FILE, CHATEAU_COORDS, MAX_DISTANCE_KM)
            with open('points_cache.json', 'w') as f:
                json.dump(points, f)

        for point in points:
            if not all(key in point for key in ['id', 'lat', 'lon', 'passengers', 'arrival_time']):
                raise ValueError(f"Point invalide: {point}")
            if not validate_time_window(point['arrival_time']):
                point['arrival_time'] = "08:00"

        return points
    except Exception as e:
        app.logger.error(f"Erreur lors du chargement des points: {str(e)}")
        raise


@app.errorhandler(Exception)
def handle_error(error):
    """Gestionnaire d'erreurs global"""
    app.logger.error(f"Erreur: {str(error)}")
    return jsonify({
        'error': str(error),
        'type': error.__class__.__name__
    }), getattr(error, 'code', 500)


@app.route('/api/points', methods=['GET'])
def get_points():
    try:
        points = load_points()
        return jsonify(points)
    except Exception as e:
        abort(500, description=str(e))


@app.route('/api/optimize', methods=['POST'])
def optimize_routes():
    try:
        config = request.json or {}

        num_drivers = min(max(1, config.get('num_drivers', 3)), 5)
        capacity = min(max(4, config.get('capacity_per_driver', 8)), 12)
        max_distance = min(max(5, config.get('max_distance_km', 15)), 20)

        optimizer.num_drivers = num_drivers
        optimizer.capacity_per_driver = capacity
        optimizer.max_distance_km = max_distance

        points = load_points()
        manager, routing, solution, data = optimizer.solve(points)

        if not solution:
            return jsonify({
                'error': 'Impossible de trouver une solution avec ces contraintes',
                'type': 'OptimizationError'
            }), 400

        routes = visualizer.extract_routes(manager, routing, solution, data)

        route_df = pd.DataFrame(routes['routes_details'])
        route_df.to_csv("routes_optimisees.csv", index=False)

        os.makedirs('static', exist_ok=True)
        map_file = "static/map.html"
        visualizer.create_map(points, routes['routes']).save(map_file)

        return jsonify({
            'routes': routes['routes'],
            'total_distance': routes['total_distance'],
            'total_passengers': routes['total_passengers'],
            'map_url': '/static/map.html',
            'stats': {
                'num_drivers': num_drivers,
                'capacity_per_driver': capacity,
                'max_distance_km': max_distance,
                'total_points': len(points)
            }
        })
    except Exception as e:
        abort(500, description=str(e))


@app.route('/api/map', methods=['GET'])
def get_map():
    try:
        return send_file('static/map.html')
    except FileNotFoundError:
        abort(404, description="Carte non générée")


@app.route('/api/driver/<int:driver_id>', methods=['GET'])
def get_driver_route(driver_id):
    try:
        if not os.path.exists('routes_optimisees.csv'):
            abort(404, description="Aucun itinéraire optimisé disponible")

        routes_df = pd.read_csv('routes_optimisees.csv')
        driver_routes = routes_df[routes_df['driver_id']
                                  == driver_id].to_dict('records')

        if not driver_routes:
            abort(
                404, description=f"Aucun itinéraire trouvé pour le chauffeur {driver_id}")

        return jsonify(driver_routes)
    except Exception as e:
        abort(500, description=str(e))


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
