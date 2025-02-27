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
        self.arrival_window = (8, 12)  # 8h à 12h
        self.departure_window = (14, 16)  # 14h à 16h
        
    def validate_points(self, points):
        """Valide les points avant l'optimisation"""
        if not points:
            raise ValueError("Aucun point à optimiser")
            
        total_passengers = sum(p['passengers'] for p in points)
        total_capacity = self.num_drivers * self.capacity_per_driver
        
        if total_passengers > total_capacity:
            raise ValueError(
                f"Capacité totale insuffisante. {total_passengers} passagers pour {total_capacity} places"
            )
            
        for point in points:
            distance = self.haversine(
                self.depot_coords[1], self.depot_coords[0],
                point['lon'], point['lat']
            )
            if distance > self.max_distance_km:
                raise ValueError(
                    f"Point {point['name']} trop éloigné ({distance:.2f} km > {self.max_distance_km} km)"
                )
    
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
        try:
            self.validate_points(points)
            
            locations = [self.depot_coords] + [(p['lat'], p['lon']) for p in points]
            distance_matrix = self.build_distance_matrix(locations)
            
            demands = [0]  # Dépôt n'a pas de demande
            time_windows = [(0, 24*60)]  # Dépôt ouvert toute la journée
            
            for p in points:
                demands.append(p['passengers'])
                # Convertir l'heure d'arrivée en minutes
                arrival_time = list(map(int, p['arrival_time'].split(':')))
                arrival_minutes = arrival_time[0] * 60 + arrival_time[1]
                
                # Vérifier la fenêtre horaire
                if not (self.arrival_window[0] * 60 <= arrival_minutes <= self.arrival_window[1] * 60):
                    arrival_minutes = self.arrival_window[0] * 60
                
                time_windows.append((arrival_minutes, arrival_minutes + 30))
            
            return {
                'distance_matrix': distance_matrix,
                'demands': demands,
                'vehicle_capacities': [self.capacity_per_driver] * self.num_drivers,
                'num_vehicles': self.num_drivers,
                'depot': 0,
                'points': points,
                'time_windows': time_windows
            }
        except Exception as e:
            raise ValueError(f"Erreur lors de la préparation des données: {str(e)}")
    
    def solve(self, points, time_limit=120, strategies=None):
        """Résout le problème VRP avec plusieurs stratégies"""
        try:
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
            
            # Fonction de coût (distance)
            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return int(data['distance_matrix'][from_node][to_node])
            
            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # Contrainte de capacité
            def demand_callback(from_index):
                from_node = manager.IndexToNode(from_index)
                return data['demands'][from_node]
            
            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,
                [cap * 3 for cap in data['vehicle_capacities']],
                True,
                'Capacity'
            )
            
            # Contrainte de temps
            def time_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                # Convertir la distance en temps (supposons 30km/h en moyenne)
                return int(data['distance_matrix'][from_node][to_node] * 2)  # 2 minutes par km
            
            time_callback_index = routing.RegisterTransitCallback(time_callback)
            routing.AddDimension(
                time_callback_index,
                30,  # slack (temps d'attente autorisé)
                24 * 60,  # max time per vehicle
                False,  # don't force start cumul to zero
                'Time'
            )
            time_dimension = routing.GetDimensionOrDie('Time')
            
            # Ajouter les fenêtres de temps
            for location_idx, time_window in enumerate(data['time_windows']):
                index = manager.NodeToIndex(location_idx)
                time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
            
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
            
            if not best_solution:
                raise ValueError(
                    "Impossible de trouver une solution. Essayez d'augmenter le nombre de chauffeurs ou la capacité."
                )
            
            return manager, routing, best_solution, data
            
        except Exception as e:
            raise ValueError(f"Erreur lors de l'optimisation: {str(e)}")