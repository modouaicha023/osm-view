import requests
import folium
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import os
from dotenv import load_dotenv

load_dotenv(".env")
# ------------------- 1. Configuration -------------------
# Coordonnées du Château de Dinan
CHATEAU_DINAN = (48.4541, -2.0474)  # Latitude, Longitude
MAX_DISTANCE_KM = 15  # Distance maximale autorisée autour du château
VEHICLE_CAPACITY = 8  # Capacité maximale de personnes par véhicule
NUM_DRIVERS = 3  # Nombre de chauffeurs disponibles

# Horaires d'ouverture (en minutes depuis minuit)
ARRIVEE_DEBUT = 8 * 60  # 8h00
ARRIVEE_FIN = 12 * 60  # 12h00
DEPART_DEBUT = 14 * 60  # 14h00
DEPART_FIN = 16 * 60  # 16h00

ORS_API_KEY = os.getenv("ORS_API_KEY")

# Vérification que la clé est bien récupérée
if not ORS_API_KEY:
    raise ValueError("La clé API ORS_API_KEY n'a pas été trouvée dans le fichier .env")

# ------------------- 2. Fonctions pour les données OSM -------------------
def get_route_details(start_coords, end_coords):
    """
    Récupère les détails d'un trajet entre deux points en utilisant OpenRouteService.
    Retourne le trajet, la distance et la durée.
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    params = {
        "api_key": ORS_API_KEY,
        "start": f"{start_coords[1]},{start_coords[0]}",
        "end": f"{end_coords[1]},{end_coords[0]}"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "features" in data and len(data["features"]) > 0:
            feature = data["features"][0]
            geometry = feature["geometry"]
            properties = feature["properties"]
            
            # Extraction des coordonnées
            coordinates = geometry["coordinates"]
            route = [(lat, lon) for lon, lat in coordinates]  # Conversion lon/lat -> lat/lon
            
            # Extraction de la distance (en mètres) et de la durée (en secondes)
            distance = properties["summary"]["distance"]  # en mètres
            duration = properties["summary"]["duration"]  # en secondes
            
            return {
                "route": route,
                "distance": distance / 1000,  # Conversion en kilomètres
                "duration": duration / 60     # Conversion en minutes
            }
        else:
            print("Erreur lors de la récupération du trajet:", data)
            return None
    except Exception as e:
        print(f"Erreur de requête: {e}")
        return None

def create_distance_matrix(locations):
    """
    Crée une matrice de distances réelles entre tous les points.
    """
    n = len(locations)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0
            else:
                route_details = get_route_details(locations[i], locations[j])
                if route_details:
                    matrix[i][j] = route_details["distance"]
                else:
                    # Distance à vol d'oiseau si l'API échoue
                    matrix[i][j] = haversine_distance(locations[i], locations[j])
    
    return matrix

def haversine_distance(point1, point2):
    """
    Calcule la distance à vol d'oiseau entre deux points (latitude, longitude).
    """
    # Rayon de la Terre en km
    earth_radius = 6371.0
    
    # Conversion en radians
    lat1 = np.radians(point1[0])
    lon1 = np.radians(point1[1])
    lat2 = np.radians(point2[0])
    lon2 = np.radians(point2[1])
    
    # Différences
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Formule haversine
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distance = earth_radius * c
    
    return distance

def generate_sample_passengers(num_passengers, chateau_coords, max_distance):
    """
    Génère des données d'exemple pour les passagers autour du château.
    """
    passengers = []
    
    for i in range(num_passengers):
        # Génération aléatoire d'un point dans un cercle de rayon max_distance
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(0, max_distance)
        
        # Conversion en déplacement lat/lon (approximation)
        # 111.32 km = 1 degré de latitude
        # 111.32 * cos(latitude) km = 1 degré de longitude
        lat_shift = radius / 111.32 * np.cos(angle)
        lon_shift = radius / (111.32 * np.cos(np.radians(chateau_coords[0]))) * np.sin(angle)
        
        lat = chateau_coords[0] + lat_shift
        lon = chateau_coords[1] + lon_shift
        
        # Horaire aléatoire (arrivée ou départ)
        is_arrival = np.random.choice([True, False])
        
        if is_arrival:
            # Passager qui veut arriver au château
            time_min = ARRIVEE_DEBUT - 60  # 1h avant l'ouverture
            time_max = ARRIVEE_FIN
            dest = chateau_coords
            origin = (lat, lon)
        else:
            # Passager qui veut partir du château
            time_min = DEPART_DEBUT
            time_max = DEPART_FIN + 60  # 1h après la fermeture
            origin = chateau_coords
            dest = (lat, lon)
        
        # Génération d'un horaire aléatoire
        time_window = np.random.randint(time_min, time_max)
        
        passengers.append({
            "id": i,
            "origin": origin,
            "destination": dest,
            "requested_time": time_window,
            "is_arrival": is_arrival,
            "num_people": np.random.randint(1, 3)  # 1 ou 2 personnes par demande
        })
    
    return pd.DataFrame(passengers)

# ------------------- 3. Visualisation -------------------
def visualize_routes(routes, locations, passengers_df):
    """
    Visualise les routes optimisées sur une carte Folium.
    """
    # Créer une carte centrée sur le château
    map_viz = folium.Map(location=CHATEAU_DINAN, zoom_start=13)
    
    # Ajouter le château
    folium.Marker(
        location=CHATEAU_DINAN,
        popup="Château de Dinan",
        icon=folium.Icon(color="black", icon="fort-awesome", prefix="fa")
    ).add_to(map_viz)
    
    # Couleurs pour les différentes routes
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred']
    
    # Pour chaque chauffeur
    for driver_idx, route in enumerate(routes):
        driver_color = colors[driver_idx % len(colors)]
        
        # Pour chaque segment de la route
        for i in range(len(route) - 1):
            start_idx = route[i]
            end_idx = route[i + 1]
            
            # Récupération des coordonnées
            start_coords = locations[start_idx]
            end_coords = locations[end_idx]
            
            # Obtention du trajet détaillé
            route_details = get_route_details(start_coords, end_coords)
            
            if route_details:
                # Tracer le trajet
                folium.PolyLine(
                    locations=route_details["route"],
                    color=driver_color,
                    weight=3,
                    opacity=0.7,
                    popup=f"Chauffeur {driver_idx+1}: {route_details['distance']:.1f} km"
                ).add_to(map_viz)
            
            # Ajouter des marqueurs pour les points d'arrêt
            if i > 0:  # Pas pour le dépôt
                passenger_info = passengers_df[passengers_df['id'] == start_idx - 1].iloc[0]
                is_arrival = passenger_info['is_arrival']
                num_people = passenger_info['num_people']
                
                if is_arrival:
                    icon_color = "green"
                    icon_type = "male"
                    popup_text = f"Prise en charge: {num_people} personne(s)"
                else:
                    icon_color = "red"
                    icon_type = "sign-out"
                    popup_text = f"Dépose: {num_people} personne(s)"
                
                folium.Marker(
                    location=start_coords,
                    popup=popup_text,
                    icon=folium.Icon(color=icon_color, icon=icon_type, prefix="fa")
                ).add_to(map_viz)
    
    # Ajouter un cercle de 15km autour du château
    folium.Circle(
        location=CHATEAU_DINAN,
        radius=MAX_DISTANCE_KM * 1000,  # Rayon en mètres
        color="gray",
        fill=True,
        fill_opacity=0.1
    ).add_to(map_viz)
    
    return map_viz

# ------------------- 4. Optimisation avec OR-Tools -------------------
def optimize_vehicle_routes(passengers_df):
    """
    Optimise les routes des véhicules avec OR-Tools en tenant compte des contraintes.
    """
    # Préparation des données
    # Le dépôt (Château) est le premier point (index 0)
    all_locations = [CHATEAU_DINAN]  
    
    # Ajouter les emplacements des passagers
    for _, row in passengers_df.iterrows():
        if row['is_arrival']:
            all_locations.append(row['origin'])
        else:
            all_locations.append(row['destination'])
    
    num_locations = len(all_locations)
    
    # Créer la matrice de distances
    distance_matrix = create_distance_matrix(all_locations)
    
    # Définir les demandes (nombre de personnes à chaque point)
    demands = [0]  # Le dépôt a une demande de 0
    for _, row in passengers_df.iterrows():
        demands.append(row['num_people'])
    
    # Configurer le gestionnaire d'index
    manager = pywrapcp.RoutingIndexManager(num_locations, NUM_DRIVERS, 0)
    routing = pywrapcp.RoutingModel(manager)
    
    # Fonction de distance
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 100)  # Conversion en centièmes de km pour entier
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Ajouter la contrainte de distance maximale
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # slack (pas de slack)
        MAX_DISTANCE_KM * 100,  # distance max en centièmes de km
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    
    # Ajouter la contrainte de capacité
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]
    
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        [VEHICLE_CAPACITY] * NUM_DRIVERS,  # capacités des véhicules
        True,  # start cumul to zero
        'Capacity')
    
    # Paramètres de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 30  # limite de temps pour la recherche
    
    # Résoudre le problème
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        routes = []
        total_distance = 0
        
        for vehicle_id in range(NUM_DRIVERS):
            route = []
            index = routing.Start(vehicle_id)
            route_distance = 0
            
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id) / 100
            
            route.append(manager.IndexToNode(index))  # Ajout du retour au dépôt
            routes.append(route)
            total_distance += route_distance
            
            print(f"Route du chauffeur {vehicle_id+1}:")
            print(f"  Points visités: {route}")
            print(f"  Distance totale: {route_distance:.2f} km")
        
        print(f"Distance totale pour tous les chauffeurs: {total_distance:.2f} km")
        return routes
    else:
        print("Aucune solution trouvée!")
        return None

# ------------------- 5. Exécution principale -------------------
def main():
    # Génération de données de test
    print("Génération des données de passagers...")
    passengers = generate_sample_passengers(20, CHATEAU_DINAN, MAX_DISTANCE_KM * 0.9)
    print(f"Nombre de passagers générés: {len(passengers)}")
    
    # Optimisation des routes
    print("Optimisation des routes...")
    routes = optimize_vehicle_routes(passengers)
    
    if routes:
        # Création de la liste complète des emplacements
        all_locations = [CHATEAU_DINAN]
        for _, row in passengers.iterrows():
            if row['is_arrival']:
                all_locations.append(row['origin'])
            else:
                all_locations.append(row['destination'])
        
        # Visualisation
        print("Création de la carte...")
        map_viz = visualize_routes(routes, all_locations, passengers)
        map_viz.save("tournees_optimisees.html")
        print("Carte générée: tournees_optimisees.html")

if __name__ == "__main__":
    main()