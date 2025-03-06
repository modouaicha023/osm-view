from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import numpy as np
import logging
import time
import random
from osm_loader import haversine
from utils import generate_random_time

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def solve_vrp(chateau_coords, points, max_points=8):
    """
    Résout le problème du VRP avec une approche simplifiée
    """
    start_time = time.time()

    # Limiter le nombre de points pour éviter la surcharge
    points = points[:max_points]
    logging.info(f"Résolution VRP avec {len(points)} points")

    # Préparer les points
    for point in points:
        point['arrival_time'] = point.get(
            'arrival_time', generate_random_time('08:00', '16:00'))
        point['name'] = point.get('name', 'Unnamed Location')

    # Préparer les localisations
    locations = [chateau_coords] + [(p['lat'], p['lon']) for p in points]
    num_locations = len(locations)

    # Matrice de distances
    distance_matrix = np.zeros((num_locations, num_locations))
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                distance_matrix[i][j] = haversine(
                    locations[i][1], locations[i][0],
                    locations[j][1], locations[j][0]
                ) * 1000  # en mètres

    # Paramètres de base
    num_vehicles = 3
    vehicle_capacity = 8
    vehicle_capacities = [vehicle_capacity] * num_vehicles

    # Demandes (passagers)
    demands = [0] + [p.get('passengers', 1) for p in points]

    # Fenêtres horaires simplifiées
    time_windows = [(0, 600)]  # 10 heures de plage
    for p in points:
        arrival_time = p.get('arrival_time', '08:00')
        hours, minutes = map(int, arrival_time.split(':'))
        min_time = hours * 60 + minutes
        # 2h de fenêtre par point
        time_windows.append((min_time, min_time + 120))

    try:
        # Gestionnaire de routage
        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix), num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        # Fonction de distance
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(
            distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Contrainte de capacité
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(
            demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index, 0, vehicle_capacities, True, "Capacity"
        )

        # Paramètres de recherche simplifiés
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30  # Limite de 30 secondes

        # Résolution
        solution = routing.SolveWithParameters(search_parameters)

        # Si pas de solution, on génère une route simple
        if not solution:
            logging.warning(
                "Aucune solution optimale trouvée. Génération d'une route simple.")
            return [
                points[i:i+len(points)//num_vehicles]
                for i in range(0, len(points), len(points)//num_vehicles)
            ]

        # Construction des routes
        routes = []
        for vehicle_id in range(num_vehicles):
            route = []
            index = routing.Start(vehicle_id)
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                if node_index != 0:  # Ignorer le dépôt
                    point = points[node_index - 1]
                    route.append({
                        "lat": point["lat"],
                        "lon": point["lon"],
                        "name": point.get("name", "Point"),
                        "arrival_time": point.get("arrival_time", "")
                    })
                index = solution.Value(routing.NextVar(index))
            routes.append(route)

        end_time = time.time()
        logging.info(
            f"Temps de résolution : {end_time - start_time:.2f} secondes")
        return routes

    except Exception as e:
        logging.error(f"Erreur lors de la résolution VRP : {e}")
        # Fallback: route simple aléatoire
        return [
            random.sample(points, len(points)//num_vehicles)
            for _ in range(num_vehicles)
        ]

# Ajout d'un fallback simple si tout échoue


def simple_route_distribution(chateau_coords, points):
    """
    Distribution simple des points si VRP échoue
    """
    points = points[:8]  # Limiter à 8 points
    num_vehicles = 2
    routes = [
        points[i:i+len(points)//num_vehicles]
        for i in range(0, len(points), len(points)//num_vehicles)
    ]
    return routes
