from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import numpy as np
from osm_loader import haversine


def solve_vrp(chateau_coords, points):
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

    demands = [0] + [p['passengers'] for p in points]
    vehicle_capacities = [8] * 3

    data = {
        "distance_matrix": distance_matrix,
        "demands": demands,
        "num_vehicles": 3,
        "depot": 0,
        "vehicle_capacities": vehicle_capacities
    }

    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]),
        data["num_vehicles"],
        data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(data["distance_matrix"][from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.SAVINGS
    )
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return []

    routes = []
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index != 0:
                point = points[node_index - 1]
                route.append({
                    "lat": point["lat"],
                    "lon": point["lon"],
                    "name": point["name"]
                })
            index = solution.Value(routing.NextVar(index))
        routes.append(route)

    return routes
