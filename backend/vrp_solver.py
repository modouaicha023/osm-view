from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import numpy as np
import logging
from osm_loader import haversine

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def solve_vrp(chateau_coords, points):
    """
    Résout le problème du VRP en prenant en compte les fenêtres horaires et la capacité des véhicules.
    """
    locations = [chateau_coords] + [(p['lat'], p['lon']) for p in points]
    num_locations = len(locations)

    # Création de la matrice de distances
    distance_matrix = np.zeros((num_locations, num_locations))
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                distance_matrix[i][j] = haversine(
                    locations[i][1], locations[i][0],
                    locations[j][1], locations[j][0]
                ) * 1000  # Conversion en mètres

    demands = [0] + [p['passengers'] for p in points]
    vehicle_capacities = [8] * 3
    num_vehicles = 3

    # Fenêtres horaires
    # Le château est ouvert de 8h (480 min) à 16h (960 min)
    time_windows = [(0, 480)]
    for p in points:
        # Matin ou après-midi
        min_time = 480 if p["arrival_time"] >= "08:00" else 840
        max_time = min_time + 240  # Plage de 4h
        time_windows.append((min_time, max_time))

    data = {
        "distance_matrix": distance_matrix,
        "demands": demands,
        "num_vehicles": num_vehicles,
        "depot": 0,
        "vehicle_capacities": vehicle_capacities,
        "time_windows": time_windows,
    }

    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix), num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    # Fonction de coût : distance
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Ajout des contraintes de capacité
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index, 0, vehicle_capacities, True, "Capacity"
    )

    # Ajout des fenêtres horaires
    def time_callback(from_index, to_index):
        return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)] // 100

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        30,  # Temps d'attente max à un arrêt
        960,  # Plage de temps max (16h)
        False,
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    for i, window in enumerate(time_windows):
        index = manager.NodeToIndex(i)
        time_dimension.CumulVar(index).SetRange(window[0], window[1])

    # Paramètres de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.SAVINGS
    )

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        logging.warning("Aucune solution trouvée.")
        return []

    routes = []
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index != 0:
                point = points[node_index - 1]
                route.append({
                    "lat": point["lat"],
                    "lon": point["lon"],
                    "name": point["name"],
                    "arrival_time": point["arrival_time"]
                })
            index = solution.Value(routing.NextVar(index))
        routes.append(route)

    return routes
