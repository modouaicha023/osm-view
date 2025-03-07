import folium
from folium import plugins
import pandas as pd


class RouteVisualizer:
    def __init__(self, depot_coords, max_distance_km=15):
        self.depot_coords = depot_coords
        self.max_distance_km = max_distance_km
        self.colors = ['green', 'purple', 'orange',
                       'cadetblue', 'darkred', 'black', 'pink']

    def create_map(self, points_data, routes=None):
        """
        Crée une carte Folium avec le dépôt et les points
        """
        map_viz = folium.Map(
            location=[self.depot_coords[0], self.depot_coords[1]], zoom_start=13)

        folium.Marker(
            location=[self.depot_coords[0], self.depot_coords[1]],
            popup="Château de Dinan",
            icon=folium.Icon(color="red", icon="building", prefix="fa")
        ).add_to(map_viz)

        folium.Circle(
            location=[self.depot_coords[0], self.depot_coords[1]],
            radius=self.max_distance_km * 1000,
            color="#3186cc",
            fill=True,
            fill_color="#3186cc",
            fill_opacity=0.1,
            popup=f"Zone de {self.max_distance_km} km"
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

        if routes:
            for vehicle_id, route in enumerate(routes):
                color = self.colors[vehicle_id % len(self.colors)]

                folium.PolyLine(
                    locations=route['points'],
                    color=color,
                    weight=4,
                    opacity=0.8,
                    popup=f"Chauffeur {vehicle_id}: {route['distance']:.2f} km, {route['load']} passagers"
                ).add_to(map_viz)

                for i, point in enumerate(route['points']):
                    if i > 0 and i < len(route['points']) - 1:
                        folium.Marker(
                            location=point,
                            icon=folium.DivIcon(
                                icon_size=(30, 30),
                                icon_anchor=(15, 15),
                                html=f'<div style="background-color:{color};color:white;width:25px;'
                                     f'height:25px;border-radius:50%;display:flex;align-items:center;justify-content:center;'
                                     f'font-weight:bold;font-size:12px;">{i}</div>',
                                class_name=f"stop-marker-{vehicle_id}-{i}"
                            ),
                            popup=f"Arrêt {i}: {route['stops'][i]['name']}"
                        ).add_to(map_viz)

                for i in range(len(route['points']) - 1):
                    plugins.AntPath(
                        locations=[route['points'][i], route['points'][i+1]],
                        dash_array=[10, 20],
                        delay=1000,
                        color=color,
                        pulse_color='#FFFFFF',
                        weight=4
                    ).add_to(map_viz)

                folium.Marker(
                    location=[self.depot_coords[0], self.depot_coords[1]],
                    popup=f"Départ chauffeur {vehicle_id}",
                    icon=folium.Icon(color=color, icon='car', prefix='fa')
                ).add_to(map_viz)

        return map_viz

    def extract_routes(self, manager, routing, solution, data):
        """
        Extrait les informations de routes depuis la solution
        """
        if not solution:
            return None

        routes = []
        routes_details = []
        total_distance = 0
        total_passengers = 0

        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_load = 0

            route_points = []
            route_points.append([self.depot_coords[0], self.depot_coords[1]])

            stop_sequence = []
            stop_sequence.append({
                "coords": [self.depot_coords[0], self.depot_coords[1]],
                "name": "Château de Dinan",
                "stop_num": 0
            })

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)

                if node_index != 0:
                    route_load += data['demands'][node_index]
                    point = data['points'][node_index - 1]

                    route_points.append([point['lat'], point['lon']])

                    stop_sequence.append({
                        "coords": [point['lat'], point['lon']],
                        "name": point['name'],
                        "stop_num": len(stop_sequence),
                        "passengers": point['passengers']
                    })

                    routes_details.append({
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
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id) / 1000

            route_points.append([self.depot_coords[0], self.depot_coords[1]])
            stop_sequence.append({
                "coords": [self.depot_coords[0], self.depot_coords[1]],
                "name": "Château de Dinan (retour)",
                "stop_num": len(stop_sequence)
            })

            total_distance += route_distance
            total_passengers += route_load

            routes.append({
                'driver_id': vehicle_id,
                'points': route_points,
                'stops': stop_sequence,
                'distance': route_distance,
                'load': route_load
            })

        return {
            'routes': routes,
            'routes_details': routes_details,
            'total_distance': total_distance,
            'total_passengers': total_passengers
        }
