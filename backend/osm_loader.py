import json
import random
from math import radians, cos, sin, asin, sqrt
from utils import generate_random_time
import logging


def haversine(lon1, lat1, lon2, lat2):
    """
    Calcule la distance en kilomètres entre deux points en utilisant leurs coordonnées latitude/longitude.
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


def load_osm_data(geojson_file, chateau_coords, max_distance_km, max_points=50):
    """
    Charge les données OSM et filtre les points dans le rayon maximum.
    """
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    points = []
    for feature in data['features']:
        coords = None
        name = feature.get('properties', {}).get('name', 'Unnamed Location')

        if feature['geometry']['type'] == 'Point':
            coords = (feature['geometry']['coordinates'][1],
                      feature['geometry']['coordinates'][0])
        elif feature['geometry']['type'] == 'Polygon':
            coords = (feature['geometry']['coordinates'][0][0]
                      [1], feature['geometry']['coordinates'][0][0][0])

        if coords:
            distance = haversine(
                chateau_coords[1], chateau_coords[0], coords[1], coords[0])

            if distance <= max_distance_km:
                passengers = random.randint(1, 3)
                points.append({
                    'lat': coords[0],
                    'lon': coords[1],
                    'passengers': passengers,
                    'distance_to_chateau': distance,
                    'name': name,
                    'arrival_time': generate_random_time('08:00', '16:00')
                })
    logging.info("done osm")
    points = points[:max_points]
    return points
