import folium
import numpy as np
import pandas as pd
import json
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from math import radians, cos, sin, asin, sqrt
import random
from folium import plugins

CHATEAU_COORDS = (48.45038746219548, -2.0447748346342434)
MAX_DISTANCE_KM = 15
NUM_DRIVERS = 3
CAPACITY_PER_DRIVER = 8
ARRIVAL_WINDOW = ("8:00", "12:00")
DEPARTURE_WINDOW = ("14:00", "16:00")

def haversine(lon1, lat1, lon2, lat2):
    """
    Calcule la distance en kilomètres entre deux points
    en utilisant leurs coordonnées latitude/longitude
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 
    return c * r

def load_osm_data(geojson_file, chateau_coords, max_distance_km):
    """
    Charge les données OSM et filtre les points dans le rayon maximum
    """
    with open(geojson_file, 'r') as f:
        data = json.load(f)
    
    points = []
    point_id = 0
    
    for feature in data['features']:
        coords = None
        
        if feature['geometry']['type'] == 'Point':
            coords = (feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0])
        elif feature['geometry']['type'] == 'Polygon' and len(feature['geometry']['coordinates'][0]) > 0:
            coords = (feature['geometry']['coordinates'][0][0][1], feature['geometry']['coordinates'][0][0][0])
        elif feature['geometry']['type'] == 'MultiPolygon' and len(feature['geometry']['coordinates']) > 0 and len(feature['geometry']['coordinates'][0]) > 0:
            coords = (feature['geometry']['coordinates'][0][0][0][1], feature['geometry']['coordinates'][0][0][0][0])
        
        if coords:
            distance = haversine(chateau_coords[1], chateau_coords[0], coords[1], coords[0])
            
            if distance <= max_distance_km:
                poi_type = None
                if 'highway' in feature['properties']:
                    poi_type = feature['properties']['highway']
                elif 'amenity' in feature['properties']:
                    poi_type = feature['properties']['amenity']
                else:
                    for key in ['name', 'building', 'shop', 'leisure', 'tourism']:
                        if key in feature['properties']:
                            poi_type = f"{key}:{feature['properties'][key]}"
                            break
                    
                    if not poi_type:
                        poi_type = feature['geometry']['type']
                
              
                passengers = random.randint(1, 3)
                
                arrival_hour = random.randint(8, 11)
                arrival_minute = random.randint(0, 59)
                if arrival_hour == 11 and arrival_minute > 30:
                    arrival_minute = 30  
                arrival_time = f"{arrival_hour:02d}:{arrival_minute:02d}"
                
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
    
    if len(points) > 30:
        random.shuffle(points)
        points = points[:30]
    
    return points

def create_map(chateau_coords, points_data):
    """
    Crée une carte Folium avec le château et les points de ramassage
    """
    map_viz = folium.Map(location=[chateau_coords[0], chateau_coords[1]], zoom_start=13)
    
    folium.Marker(
        location=[chateau_coords[0], chateau_coords[1]],
        popup="Château de Dinan",
        icon=folium.Icon(color="red", icon="building", prefix="fa")
    ).add_to(map_viz)
    
    folium.Circle(
        location=[chateau_coords[0], chateau_coords[1]],
        radius=MAX_DISTANCE_KM * 1000,  
        color="#3186cc",
        fill=True,
        fill_color="#3186cc",
        fill_opacity=0.1,
        popup=f"Zone de {MAX_DISTANCE_KM} km"
    ).add_to(map_viz)
    
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

def prepare_vrp_data(chateau_coords, points):
    """
    Prépare les données au format requis pour OR-Tools
    """
    locations = [chateau_coords] + [(p['lat'], p['lon']) for p in points]
    num_locations = len(locations)
    distance_matrix = np.zeros((num_locations, num_locations))
    
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                distance_matrix[i][j] = haversine(
                    locations[i][1], locations[i][0],
                    locations[j][1], locations[j][0]
                ) * 1000
    
    demands = [0]
    for p in points:
        demands.append(p['passengers'])
    
    data = {
        'distance_matrix': distance_matrix,
        'demands': demands,
        'vehicle_capacities': [CAPACITY_PER_DRIVER] * NUM_DRIVERS,
        'num_vehicles': NUM_DRIVERS,
        'depot': 0  
    }
    
    return data

def solve_vrp(data):
    """
    Résout le problème de routage de véhicules avec OR-Tools avec plus de flexibilité
    """
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'],
        0
    )
    routing = pywrapcp.RoutingModel(manager)
    
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(data['distance_matrix'][from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]
    
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    
    vehicle_capacities = [cap * 3 for cap in data['vehicle_capacities']]
    
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  
        vehicle_capacities, 
        True,  
        'Capacity'
    )
    
    max_distance = 50000  
    routing.AddDimension(
        transit_callback_index,
        0,  
        max_distance,
        True,  
        'Distance'
    )
    
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.SAVINGS
    )
    
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    
    search_parameters.time_limit.seconds = 120
    
    solution = routing.SolveWithParameters(search_parameters)
    
    if not solution:
        print("Pas de solution, tentative avec AUTOMATIC...")
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        )
        solution = routing.SolveWithParameters(search_parameters)
    
    return manager, routing, solution

def display_routes(manager, routing, solution, points, map_viz):
    """
    Affiche les itinéraires calculés sur la carte avec indication de direction
    """
    if not solution:
        print("Pas de solution trouvée !")
        return
    
    colors = ['green', 'purple', 'orange', 'cadetblue', 'darkred', 'black', 'pink']
    
    routes_df = []
    
    print(f"Solution trouvée !")
    total_distance = 0
    
    for vehicle_id in range(routing.vehicles()):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_load = 0
        
        route_points = []
        route_points.append([CHATEAU_COORDS[0], CHATEAU_COORDS[1]])
        
        route_str = f"Route du chauffeur {vehicle_id}:\n"
        route_str += f"  Château de Dinan"
        
        stop_sequence = []
        stop_sequence.append({"coords": [CHATEAU_COORDS[0], CHATEAU_COORDS[1]], "name": "Château de Dinan", "stop_num": 0})
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index != 0: 
                route_load += data['demands'][node_index]
                point = points[node_index - 1] 
                route_str += f" -> {point['name']} ({point['passengers']} passagers)"
                
                route_points.append([point['lat'], point['lon']])
                
                stop_sequence.append({
                    "coords": [point['lat'], point['lon']], 
                    "name": point['name'], 
                    "stop_num": len(stop_sequence)
                })
                
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
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id) / 1000 
        
        route_points.append([CHATEAU_COORDS[0], CHATEAU_COORDS[1]])
        stop_sequence.append({"coords": [CHATEAU_COORDS[0], CHATEAU_COORDS[1]], "name": "Château de Dinan (retour)", "stop_num": len(stop_sequence)})
        
        route_str += f" -> Château de Dinan"
        route_str += f"\n  Distance: {route_distance:.2f} km"
        route_str += f"\n  Charge: {route_load}/{CAPACITY_PER_DRIVER} passagers"
        print(route_str)
        
        total_distance += route_distance
        
        print(f"Chauffeur {vehicle_id}: {len(route_points)} points, charge: {route_load}/{CAPACITY_PER_DRIVER}")
        
        if len(route_points) > 2:
            print(f"Tracé de l'itinéraire pour le chauffeur {vehicle_id} avec {len(route_points)} points")
            
            print(f"Premier point: {route_points[0]}, Deuxième point: {route_points[1]}")
            
            folium.PolyLine(
                locations=route_points,
                color=colors[vehicle_id % len(colors)],
                weight=4,
                opacity=0.8,
                popup=f"Chauffeur {vehicle_id}: {route_distance:.2f} km, {route_load} passagers"
            ).add_to(map_viz)
            
            for i in range(len(route_points) - 1):
                mid_point = [(route_points[i][0] + route_points[i+1][0]) / 2, 
                             (route_points[i][1] + route_points[i+1][1]) / 2]
                
                folium.Marker(
                    location=route_points[i],
                    icon=folium.DivIcon(
                        icon_size=(30, 30),
                        icon_anchor=(15, 15),
                        html=f'<div style="background-color:{colors[vehicle_id % len(colors)]};color:white;width:25px;'
                             f'height:25px;border-radius:50%;display:flex;align-items:center;justify-content:center;'
                             f'font-weight:bold;font-size:12px;">{i}</div>',
                        class_name=f"stop-marker-{vehicle_id}-{i}"
                    ),
                    popup=f"Arrêt {i}: {stop_sequence[i]['name']}"
                ).add_to(map_viz)
                
                plugins.AntPath(
                    locations=[route_points[i], route_points[i+1]],
                    dash_array=[10, 20],
                    delay=1000,
                    color=colors[vehicle_id % len(colors)],
                    pulse_color='#FFFFFF',
                    weight=4
                ).add_to(map_viz)
            
            folium.Marker(
                location=route_points[-1],
                icon=folium.DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=f'<div style="background-color:{colors[vehicle_id % len(colors)]};color:white;width:25px;'
                         f'height:25px;border-radius:50%;display:flex;align-items:center;justify-content:center;'
                         f'font-weight:bold;font-size:12px;">{len(route_points)-1}</div>',
                    class_name=f"stop-marker-{vehicle_id}-end"
                ),
                popup=f"Retour au château (chauffeur {vehicle_id})"
            ).add_to(map_viz)
            
            folium.Marker(
                location=[CHATEAU_COORDS[0], CHATEAU_COORDS[1]],
                popup=f"Départ chauffeur {vehicle_id}",
                icon=folium.Icon(color=colors[vehicle_id % len(colors)], icon='car', prefix='fa')
            ).add_to(map_viz)
    
    print(f"Distance totale: {total_distance:.2f} km")
    return pd.DataFrame(routes_df) if routes_df else None
print("Chargement des données OSM...")
geojson_file = 'dinan_osm_data.geojson'
points = load_osm_data(geojson_file, CHATEAU_COORDS, MAX_DISTANCE_KM)
print(f"{len(points)} points trouvés dans le rayon de {MAX_DISTANCE_KM} km.")

if len(points) == 0:
    print("Aucun point trouvé dans le rayon. Vérifiez les données OSM ou augmentez le rayon.")
    exit()

print("Création de la carte...")
map_viz = create_map(CHATEAU_COORDS, points)

print("Préparation des données pour l'optimisation...")
data = prepare_vrp_data(CHATEAU_COORDS, points)

print("Résolution du problème de routage...")
manager, routing, solution = solve_vrp(data)

if solution:
    print("Tracé des itinéraires optimisés...")
    routes_df = display_routes(manager, routing, solution, points, map_viz)
    if routes_df is not None:
        routes_df.to_csv("routes_optimisees.csv", index=False)
        print("Données des routes sauvegardées dans 'routes_optimisees.csv'")
else:
    print("Pas de solution trouvée. Vérifiez les contraintes du problème.")

map_viz.save("index.html")
print(f"Carte générée avec les itinéraires optimisés dans 'index.html'")