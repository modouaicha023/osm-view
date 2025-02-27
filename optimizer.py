# optimizer.py
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from math import radians, cos, sin, asin, sqrt
import time

class RouteOptimizer:
    def __init__(self, depot_coords, max_distance_km=15, num_drivers=3, capacity_per_driver=8):
        self.depot_coords = depot_coords
        self.max_distance_km = max_distance_km
        self.num_drivers = num_drivers
        self.capacity_per_driver = capacity_per_driver
        
    def haversine(self, lon1, lat1, lon2, lat2):
        """Calcule la distance en kilomètres entre deux points"""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371 
        return c * r
        
    def build_distance_matrix(self, locations):
        """Construit la matrice de distance entre tous les points"""
        num_locations = len(locations)
        matrix = np.zeros((num_locations, num_locations))
        
        for i in range(num_locations):
            for j in range(num_locations):
                if i != j:
                    matrix[i][j] = self.haversine(
                        locations[i][1], locations[i][0],
                        locations[j][1], locations[j][0]
                    ) * 1000  # Convertir en mètres pour OR-Tools
        
        return matrix
    
    def prepare_data(self, points):
        """Prépare les données pour OR-Tools"""
        locations = [self.depot_coords] + [(p['lat'], p['lon']) for p in points]
        distance_matrix = self.build_distance_matrix(locations)
        
        demands = [0]  # Dépôt n'a pas de demande
        for p in points:
            demands.append(p['passengers'])
        
        data = {
            'distance_matrix': distance_matrix,
            'demands': demands,
            'vehicle_capacities': [self.capacity_per_driver] * self.num_drivers,
            'num_vehicles': self.num_drivers,
            'depot': 0,
            'points': points
        }
        
        return data
    
    def solve(self, points, time_limit=120, strategies=None):
        """Résout le problème VRP avec plusieurs stratégies"""
        if strategies is None:
            strategies = [
                routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
                routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
            ]
        
        data = self.prepare_data(points)
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            0
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # Définir la fonction de coût (distance)
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data['distance_matrix'][from_node][to_node])
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Ajouter la contrainte de capacité
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        # Multiplier par 3 pour donner plus de flexibilité (comme dans votre code original)
        vehicle_capacities = [cap * 3 for cap in data['vehicle_capacities']]
        
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # No slack
            vehicle_capacities, 
            True,  # Start cumul to zero
            'Capacity'
        )
        
        # Ajouter la contrainte de distance maximum
        max_distance = self.max_distance_km * 1000 * 2  # Aller-retour en mètres
        routing.AddDimension(
            transit_callback_index,
            0,  # No slack
            max_distance,
            True,  # Start cumul to zero
            'Distance'
        )
        
        # Essayer différentes stratégies
        best_solution = None
        best_cost = float('inf')
        best_strategy = None
        
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = time_limit // len(strategies)
        
        for strategy in strategies:
            search_parameters.first_solution_strategy = strategy
            start_time = time.time()
            solution = routing.SolveWithParameters(search_parameters)
            solve_time = time.time() - start_time
            
            if solution:
                cost = solution.ObjectiveValue()
                print(f"Strategy {strategy} found solution with cost {cost} in {solve_time:.2f}s")
                
                if cost < best_cost:
                    best_cost = cost
                    best_solution = solution
                    best_strategy = strategy
            else:
                print(f"Strategy {strategy} found no solution")
        
        print(f"Best strategy: {best_strategy} with cost {best_cost}")
        return manager, routing, best_solution, data