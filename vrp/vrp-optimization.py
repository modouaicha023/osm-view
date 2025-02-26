import pandas as pd
import numpy as np
import folium
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import matplotlib.pyplot as plt
import random
import colorsys

# Lire les données des clients
df_clients = pd.read_csv('./vrp/clients_dinan.csv')

# Coordonnées du Château de Dinan
CHATEAU_LAT = 48.4551
CHATEAU_LON = -2.0410
NB_CHAUFFEURS = 3
CAPACITE_VEHICULE = 8

# Créer une matrice de distance entre tous les points
def creer_matrice_distance(df):
    """Crée une matrice de distance entre tous les points (château + clients)"""
    # Ajouter le château comme premier point (indice 0)
    points = pd.DataFrame([{
        'id': 0,
        'latitude': CHATEAU_LAT, 
        'longitude': CHATEAU_LON,
        'nb_personnes': 0
    }])
    
    # Ajouter les clients
    points = pd.concat([points, df[['id', 'latitude', 'longitude', 'nb_personnes']]])
    points = points.reset_index(drop=True)
    
    n = len(points)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if i != j:
                # Calculer la distance haversine
                lat1, lon1 = points.iloc[i]['latitude'], points.iloc[i]['longitude']
                lat2, lon2 = points.iloc[j]['latitude'], points.iloc[j]['longitude']
                
                # Conversion en radians
                lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
                
                # Formule de Haversine
                R = 6371  # Rayon de la Terre en km
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                matrix[i, j] = R * c
    
    return matrix, points

def resoudre_vrp_arrivees():
    """Résout le problème VRP pour les arrivées au château (8h-12h)"""
    # Filtrer les clients qui arrivent au château entre 8h et 12h
    clients_arrivee = df_clients[df_clients['heure_arrivee'].between(8*60, 12*60-1)]
    
    # Créer la matrice de distance
    distance_matrix, points = creer_matrice_distance(clients_arrivee)
    
    # Créer les données du modèle
    data = {}
    data['distance_matrix'] = distance_matrix
    data['num_vehicles'] = NB_CHAUFFEURS
    data['depot'] = 0  # Le château est le dépôt (indice 0)
    
    # Ajouter les demandes (nombre de personnes par client)
    data['demands'] = [0]  # Le château a une demande de 0
    for i in range(1, len(points)):
        data['demands'].append(points.iloc[i]['nb_personnes'])
    
    data['vehicle_capacities'] = [CAPACITE_VEHICULE] * data['num_vehicles']
    
    # Créer le modèle de routage
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)
    
    # Fonction de coût (distance)
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Ajouter la contrainte de capacité
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]
    
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # capacity de chaque véhicule
        True,  # start cumul to zero
        'Capacity')
    
    # Ajouter la contrainte de distance maximale (15 km)
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        15,  # maximum distance
        True,  # start cumul to zero
        'Distance')
    
    # Définir la stratégie de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 30
    
    # Résoudre le problème
    solution = routing.SolveWithParameters(search_parameters)
    
    # Préparer le résultat pour la visualisation
    routes = []
    if solution:
        for vehicle_id in range(data['num_vehicles']):
            route = []
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_load = 0
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append(node_index)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                route_load += data['demands'][node_index]
            
            # Ajouter le retour au dépôt
            route.append(0)
            
            routes.append({
                'vehicle_id': vehicle_id,
                'route': route,
                'distance': route_distance,
                'load': route_load
            })
    
    return routes, points

def resoudre_vrp_departs():
    """Résout le problème VRP pour les départs du château (14h-16h)"""
    # Filtrer les clients qui partent du château entre 14h et 16h
    clients_depart = df_clients[df_clients['heure_depart'].between(14*60, 16*60-1)]
    
    # Créer la matrice de distance
    distance_matrix, points = creer_matrice_distance(clients_depart)
    
    # Même structure que pour les arrivées, mais le problème est inversé
    # Les clients partent du château vers leurs destinations
    data = {}
    data['distance_matrix'] = distance_matrix
    data['num_vehicles'] = NB_CHAUFFEURS
    data['depot'] = 0  # Le château est le dépôt (indice 0)
    
    # Ajouter les demandes (nombre de personnes par client)
    data['demands'] = [0]  # Le château a une demande de 0
    for i in range(1, len(points)):
        data['demands'].append(points.iloc[i]['nb_personnes'])
    
    data['vehicle_capacities'] = [CAPACITE_VEHICULE] * data['num_vehicles']
    
    # Créer le modèle de routage
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)
    
    # Fonction de coût (distance)
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Ajouter la contrainte de capacité
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]
    
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # capacity de chaque véhicule
        True,  # start cumul to zero
        'Capacity')
    
    # Ajouter la contrainte de distance maximale (15 km)
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        15,  # maximum distance
        True,  # start cumul to zero
        'Distance')
    
    # Définir la stratégie de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 30
    
    # Résoudre le problème
    solution = routing.SolveWithParameters(search_parameters)
    
    # Préparer le résultat pour la visualisation
    routes = []
    if solution:
        for vehicle_id in range(data['num_vehicles']):
            route = []
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_load = 0
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append(node_index)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                route_load += data['demands'][node_index]
            
            # Ajouter le retour au dépôt
            route.append(0)
            
            routes.append({
                'vehicle_id': vehicle_id,
                'route': route,
                'distance': route_distance,
                'load': route_load
            })
    
    return routes, points

# Générer des couleurs distinctes pour les routes
def generate_colors(n):
    colors = []
    for i in range(n):
        # Générer des couleurs espacées sur le spectre HSL
        hue = i / n
        lightness = 0.5
        saturation = 0.8
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        # Convertir en code hexadécimal
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        colors.append(hex_color)
    return colors

# Visualiser les routes sur une carte
def visualiser_routes(routes_arrivee, points_arrivee, routes_depart, points_depart):
    # Créer la carte centrée sur le château
    m = folium.Map(location=[CHATEAU_LAT, CHATEAU_LON], zoom_start=12)
    
    # Ajouter le château
    folium.Marker(
        location=[CHATEAU_LAT, CHATEAU_LON],
        popup="Château de Dinan",
        icon=folium.Icon(color='red', icon='building')
    ).add_to(m)
    
    # Dessiner le cercle de 15 km de rayon
    folium.Circle(
        location=[CHATEAU_LAT, CHATEAU_LON],
        radius=15000,  # En mètres
        color='blue',
        fill=True,
        fill_opacity=0.1
    ).add_to(m)
    
    # Ajouter les routes d'arrivée
    colors = generate_colors(NB_CHAUFFEURS)
    
    # Créer un groupe de couches pour les arrivées
    arrival_group = folium.FeatureGroup(name="Arrivées (8h-12h)")
    
    for i, route_data in enumerate(routes_arrivee):
        route = route_data['route']
        route_points = []
        
        for node in route:
            if node < len(points_arrivee):
                lat = points_arrivee.iloc[node]['latitude']
                lon = points_arrivee.iloc[node]['longitude']
                route_points.append([lat, lon])
                
                # Ajouter un marqueur pour chaque client (sauf le dépôt)
                if node != 0:  # Pas le dépôt
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=4,
                        color=colors[i],
                        fill=True,
                        fill_opacity=0.7,
                        popup=f"Client {points_arrivee.iloc[node]['id']}<br>"
                              f"Personnes: {points_arrivee.iloc[node]['nb_personnes']}"
                    ).add_to(arrival_group)
        
        # Tracer la route
        folium.PolyLine(
            route_points,
            color=colors[i],
            weight=4,
            opacity=0.8,
            popup=f"Chauffeur {i+1} - Arrivée<br>"
                  f"Distance: {route_data['distance']:.2f} km<br>"
                  f"Passagers: {route_data['load']}"
        ).add_to(arrival_group)
    
    arrival_group.add_to(m)
    
    # Créer un groupe de couches pour les départs
    departure_group = folium.FeatureGroup(name="Départs (14h-16h)")
    
    # Ajouter les routes de départ
    for i, route_data in enumerate(routes_depart):
        route = route_data['route']
        route_points = []
        
        for node in route:
            if node < len(points_depart):
                lat = points_depart.iloc[node]['latitude']
                lon = points_depart.iloc[node]['longitude']
                route_points.append([lat, lon])
                
                # Ajouter un marqueur pour chaque client (sauf le dépôt)
                if node != 0:  # Pas le dépôt
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=4,
                        color=colors[i],
                        fill=True,
                        fill_opacity=0.7,
                        popup=f"Client {points_depart.iloc[node]['id']}<br>"
                              f"Personnes: {points_depart.iloc[node]['nb_personnes']}"
                    ).add_to(departure_group)
        
        # Tracer la route
        folium.PolyLine(
            route_points,
            color=colors[i],
            weight=4,
            opacity=0.8,
            popup=f"Chauffeur {i+1} - Départ<br>"
                  f"Distance: {route_data['distance']:.2f} km<br>"
                  f"Passagers: {route_data['load']}"
        ).add_to(departure_group)
    
    departure_group.add_to(m)
    
    # Ajouter un contrôleur de couches
    folium.LayerControl().add_to(m)
    
    # Sauvegarder la carte
    m.save('./vrp/routes_optimisees_dinan.html')
    print("Carte des routes optimisées sauvegardée dans 'routes_optimisees_dinan.html'")

# Résoudre et visualiser
print("Résolution du problème VRP pour les arrivées...")
routes_arrivee, points_arrivee = resoudre_vrp_arrivees()

print("Résolution du problème VRP pour les départs...")
routes_depart, points_depart = resoudre_vrp_departs()

print("Visualisation des routes optimisées...")
visualiser_routes(routes_arrivee, points_arrivee, routes_depart, points_depart)

# Afficher un résumé des résultats
print("\nRésumé des routes d'arrivée (8h-12h):")
total_distance_arrivee = 0
total_passagers_arrivee = 0
for i, route in enumerate(routes_arrivee):
    print(f"Chauffeur {i+1}: {len(route['route'])-2} clients, {route['distance']:.2f} km, {route['load']} passagers")
    total_distance_arrivee += route['distance']
    total_passagers_arrivee += route['load']
print(f"Total arrivée: {total_distance_arrivee:.2f} km, {total_passagers_arrivee} passagers")

print("\nRésumé des routes de départ (14h-16h):")
total_distance_depart = 0
total_passagers_depart = 0
for i, route in enumerate(routes_depart):
    print(f"Chauffeur {i+1}: {len(route['route'])-2} clients, {route['distance']:.2f} km, {route['load']} passagers")
    total_distance_depart += route['distance']
    total_passagers_depart += route['load']
print(f"Total départ: {total_distance_depart:.2f} km, {total_passagers_depart} passagers")