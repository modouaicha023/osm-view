import folium
import numpy as np
import pandas as pd
import json
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from math import radians, cos, sin, asin, sqrt
import random

# Configuration
CHATEAU_COORDS = (48.45038746219548, -2.0447748346342434)  # Coordonnées du Château de Dinan
MAX_DISTANCE_KM = 15  # Rayon maximal de déplacement
NUM_DRIVERS = 3
CAPACITY_PER_DRIVER = 8
ARRIVAL_WINDOW = ("8:00", "12:00")
DEPARTURE_WINDOW = ("14:00", "16:00")

# Fonction pour calculer la distance entre deux points (formule de Haversine)
def haversine(lon1, lat1, lon2, lat2):
    """
    Calcule la distance en kilomètres entre deux points
    en utilisant leurs coordonnées latitude/longitude
    """
    # Convertir les degrés en radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Formule de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Rayon de la Terre en km
    return c * r

# Charger et traiter les données OSM
def load_osm_data(geojson_file, chateau_coords, max_distance_km):
    """
    Charge les données OSM et filtre les points dans le rayon maximum
    """
    with open(geojson_file, 'r') as f:
        data = json.load(f)
    
    points = []
    point_id = 0
    
    for feature in data['features']:
        # Extraire les coordonnées selon le type de géométrie
        coords = None
        
        if feature['geometry']['type'] == 'Point':
            coords = (feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0])
        elif feature['geometry']['type'] == 'Polygon' and len(feature['geometry']['coordinates'][0]) > 0:
            # Prendre le premier point du polygone
            coords = (feature['geometry']['coordinates'][0][0][1], feature['geometry']['coordinates'][0][0][0])
        elif feature['geometry']['type'] == 'MultiPolygon' and len(feature['geometry']['coordinates']) > 0 and len(feature['geometry']['coordinates'][0]) > 0:
            # Prendre le premier point du premier polygone
            coords = (feature['geometry']['coordinates'][0][0][0][1], feature['geometry']['coordinates'][0][0][0][0])
        
        if coords:
            # Calculer la distance au château
            distance = haversine(chateau_coords[1], chateau_coords[0], coords[1], coords[0])
            
            # Filtrer les points trop éloignés
            if distance <= max_distance_km:
                # Récupérer le type de point d'intérêt
                poi_type = None
                if 'highway' in feature['properties']:
                    poi_type = feature['properties']['highway']
                elif 'amenity' in feature['properties']:
                    poi_type = feature['properties']['amenity']
                else:
                    # Chercher une propriété significative
                    for key in ['name', 'building', 'shop', 'leisure', 'tourism']:
                        if key in feature['properties']:
                            poi_type = f"{key}:{feature['properties'][key]}"
                            break
                    
                    if not poi_type:
                        poi_type = feature['geometry']['type']
                
                # Générer un nombre aléatoire de passagers (1-4)
                passengers = random.randint(1, 4)
                
                # Générer une heure d'arrivée aléatoire entre 8h et 12h
                arrival_hour = random.randint(8, 11)
                arrival_minute = random.randint(0, 59)
                if arrival_hour == 11 and arrival_minute > 30:
                    arrival_minute = 30  # Pour rester dans la fenêtre de 8h à 12h
                arrival_time = f"{arrival_hour:02d}:{arrival_minute:02d}"
                
                # Récupérer le nom si disponible
                name = feature['properties'].get('name', f"Point {point_id}")
                
                points.append({
                    'id': point_id,
                    'lat': coords[0],
                    'lon': coords[1],
                    'passengers': passengers,
                    'distance_to_chateau': distance,
                    'poi_type': poi_type,
                    'arrival_time': arrival_time,
                    'name': name
                })
                
                point_id += 1
    
    # Si nous avons trop de points, on prend un échantillon
    if len(points) > 50:
        random.shuffle(points)
        points = points[:50]
    
    return points

# Créer la carte centrée sur le Château de Dinan
def create_map(chateau_coords, points_data):
    """
    Crée une carte Folium avec le château et les points de ramassage
    """
    map_viz = folium.Map(location=[chateau_coords[0], chateau_coords[1]], zoom_start=13)
    
    # Ajouter le Château comme destination principale
    folium.Marker(
        location=[chateau_coords[0], chateau_coords[1]],
        popup="Château de Dinan",
        icon=folium.Icon(color="red", icon="building", prefix="fa")
    ).add_to(map_viz)
    
    # Dessiner un cercle de rayon MAX_DISTANCE_KM
    folium.Circle(
        location=[chateau_coords[0], chateau_coords[1]],
        radius=MAX_DISTANCE_KM * 1000,  # Rayon en mètres
        color="#3186cc",
        fill=True,
        fill_color="#3186cc",
        fill_opacity=0.1,
        popup=f"Zone de {MAX_DISTANCE_KM} km"
    ).add_to(map_viz)
    
    # Ajouter les points de ramassage
    for point in points_data:
        popup_content = (f"ID: {point['id']}<br>"
                        f"Nom: {point['name']}<br>"
                        f"Type: {point['poi_type']}<br>"
                        f"Passagers: {point['passengers']}<br>"
                        f"Distance: {point['distance_to_chateau']:.2f} km<br>"
                        f"Heure d'arrivée: {point['arrival_time']}")
        
        folium.Marker(
            location=[point['lat'], point['lon']],
            popup=popup_content,
            icon=folium.Icon(color="blue", icon="user", prefix="fa")
        ).add_to(map_viz)
    
    return map_viz

# Préparer les données pour l'algorithme VRP (Vehicle Routing Problem)
def prepare_vrp_data(chateau_coords, points):
    """
    Prépare les données au format requis pour OR-Tools
    """
    # Créer la matrice de distance
    locations = [chateau_coords] + [(p['lat'], p['lon']) for p in points]
    num_locations = len(locations)
    distance_matrix = np.zeros((num_locations, num_locations))
    
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                distance_matrix[i][j] = haversine(
                    locations[i][1], locations[i][0],
                    locations[j][1], locations[j][0]
                ) * 1000  # Convertir en mètres pour OR-Tools
    
    # Demandes (nombre de passagers à ramasser)
    demands = [0]  # Le château n'a pas de demande
    for p in points:
        demands.append(p['passengers'])
    
    data = {
        'distance_matrix': distance_matrix,
        'demands': demands,
        'vehicle_capacities': [CAPACITY_PER_DRIVER] * NUM_DRIVERS,
        'num_vehicles': NUM_DRIVERS,
        'depot': 0  # Le château est le dépôt (point de départ et d'arrivée)
    }
    
    return data

# Fonction qui résout le problème VRP
def solve_vrp(data):
    """
    Résout le problème de routage de véhicules avec OR-Tools
    """
    # Créer le modèle de routage
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'],
        0  # dépôt
    )
    routing = pywrapcp.RoutingModel(manager)
    
    # Fonction de coût basée sur la distance
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        print(f"Distance callback: from_index={from_index}, to_index={to_index}, from_node={from_node}, to_node={to_node}")
        return data['distance_matrix'][from_node][to_node]

    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Ajouter les contraintes de capacité
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]
    
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # slack max
        data['vehicle_capacities'],  # capacités des véhicules
        True,  # début à zéro
        'Capacity'
    )
    
    # Paramètres de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 30
    
    # Résoudre le problème
    solution = routing.SolveWithParameters(search_parameters)
    
    return manager, routing, solution

# Fonction pour afficher et tracer les itinéraires sur la carte
def display_routes(manager, routing, solution, points, map_viz):
    """
    Affiche les itinéraires calculés sur la carte
    """
    if not solution:
        print("Pas de solution trouvée !")
        return
    
    # Couleurs pour les différents chauffeurs
    colors = ['green', 'purple', 'orange', 'cadetblue', 'darkred', 'black', 'pink']
    
    # Créer un DataFrame pour stocker les résultats
    routes_df = []
    
    print(f"Solution trouvée :")
    total_distance = 0
    
    for vehicle_id in range(routing.vehicles()):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_load = 0
        route_points = []
        
        route_points.append(CHATEAU_COORDS)  # Commencer au château
        
        route_str = f"Route du chauffeur {vehicle_id}:\n"
        route_str += f"  Château de Dinan"
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index != 0:  # Si ce n'est pas le dépôt
                route_load += data['demands'][node_index]
                point = points[node_index - 1]  # -1 car le premier point est le château
                route_str += f" -> {point['name']} ({point['passengers']} passagers)"
                route_points.append((point['lat'], point['lon']))
                routes_df.append({
                    'driver_id': vehicle_id,
                    'stop_number': len(route_points) - 1,
                    'point_id': point['id'],
                    'name': point['name'],
                    'poi_type': point['poi_type'],
                    'lat': point['lat'],
                    'lon': point['lon'],
                    'passengers': point['passengers'],
                    'distance_to_chateau': point['distance_to_chateau'],
                    'arrival_time': point['arrival_time']
                })
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id) / 1000  # km
        
        route_points.append(CHATEAU_COORDS)  # Terminer au château
        route_str += f" -> Château de Dinan"
        route_str += f"\n  Distance: {route_distance:.2f} km"
        route_str += f"\n  Charge: {route_load}/{CAPACITY_PER_DRIVER} passagers"
        print(route_str)
        
        total_distance += route_distance
        
        # Tracer l'itinéraire sur la carte
        if len(route_points) > 2:  # S'il y a au moins un point en plus du château
            folium.PolyLine(
                route_points,
                color=colors[vehicle_id % len(colors)],
                weight=4,
                opacity=0.8,
                popup=f"Chauffeur {vehicle_id}: {route_distance:.2f} km, {route_load} passagers"
            ).add_to(map_viz)
    
    print(f"Distance totale: {total_distance:.2f} km")
    return pd.DataFrame(routes_df) if routes_df else None

# Charger les données OSM
print("Chargement des données OSM...")
geojson_file = 'dinan_osm_data.geojson'
points = load_osm_data(geojson_file, CHATEAU_COORDS, MAX_DISTANCE_KM)
print(f"{len(points)} points trouvés dans le rayon de {MAX_DISTANCE_KM} km.")

if len(points) == 0:
    print("Aucun point trouvé dans le rayon. Vérifiez les données OSM ou augmentez le rayon.")
    exit()

# Créer la carte
print("Création de la carte...")
map_viz = create_map(CHATEAU_COORDS, points)

# Préparer les données pour l'optimisation VRP
print("Préparation des données pour l'optimisation...")
data = prepare_vrp_data(CHATEAU_COORDS, points)

# Résoudre le problème VRP
print("Résolution du problème de routage...")
manager, routing, solution = solve_vrp(data)

# Afficher et tracer les itinéraires
if solution:
    print("Tracé des itinéraires optimisés...")
    routes_df = display_routes(manager, routing, solution, points, map_viz)
    if routes_df is not None:
        # Sauvegarder les données des routes
        routes_df.to_csv("routes_optimisees.csv", index=False)
        print("Données des routes sauvegardées dans 'routes_optimisees.csv'")
else:
    print("Pas de solution trouvée. Vérifiez les contraintes du problème.")

# Sauvegarder la carte
map_viz.save("dinan_routes_optimisees.html")
print(f"Carte générée avec les itinéraires optimisés dans 'dinan_routes_optimisees.html'")