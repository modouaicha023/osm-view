import pandas as pd
import numpy as np
import folium
import requests
import random
from math import radians, sin, cos, sqrt, atan2

# Coordonnées du Château de Dinan
CHATEAU_LAT = 48.4551
CHATEAU_LON = -2.0410
RAYON_MAX = 15  # km

def distance_haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance en km entre deux points en utilisant la formule de Haversine"""
    R = 6371  # Rayon de la Terre en km
    
    # Conversion en radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Différence de longitude et latitude
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Formule de Haversine
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

# Générer des points aléatoires dans un rayon de 15 km autour du château
# Ces points représenteront les adresses des clients à ramasser
def generer_points_clients(nb_clients=30):
    clients = []
    
    # Pour simuler des clients, on génère des points aléatoires dans un rayon de 15 km
    for i in range(nb_clients):
        # Créer un point aléatoire
        angle = random.uniform(0, 2 * np.pi)
        rayon_km = random.uniform(1, RAYON_MAX)  # Entre 1 et 15 km du château
        
        # Conversion approximative de km en degrés (varie selon la latitude)
        # 1 degré de latitude ≈ 111 km
        # 1 degré de longitude ≈ 111 * cos(latitude) km
        lat_offset = rayon_km / 111 * np.sin(angle)
        lon_offset = rayon_km / (111 * np.cos(radians(CHATEAU_LAT))) * np.cos(angle)
        
        lat = CHATEAU_LAT + lat_offset
        lon = CHATEAU_LON + lon_offset
        
        # Vérifier que la distance est bien dans les limites
        dist = distance_haversine(CHATEAU_LAT, CHATEAU_LON, lat, lon)
        
        # Générer heure d'arrivée aléatoire entre 8h et 12h (en minutes depuis minuit)
        heure_arrivee = random.randint(8*60, 12*60-1)
        heure_depart = random.randint(14*60, 16*60-1)
        
        clients.append({
            'id': i,
            'latitude': lat,
            'longitude': lon,
            'distance_chateau': dist,
            'nb_personnes': random.randint(1, 4),  # Entre 1 et 4 personnes par client
            'heure_arrivee': heure_arrivee,  # Format minutes depuis minuit
            'heure_depart': heure_depart    # Format minutes depuis minuit
        })
    
    return pd.DataFrame(clients)

# Générer des données de clients
df_clients = generer_points_clients(30)
print(f"Nombre de clients générés: {len(df_clients)}")
print(df_clients.head())

# Enregistrer les données
df_clients.to_csv('clients_dinan.csv', index=False)

# Créer une carte pour visualiser
m = folium.Map(location=[CHATEAU_LAT, CHATEAU_LON], zoom_start=12)

# Ajouter le château comme point central
folium.Marker(
    location=[CHATEAU_LAT, CHATEAU_LON],
    popup="Château de Dinan",
    icon=folium.Icon(color='red', icon='building')
).add_to(m)

# Dessiner le cercle de 15 km de rayon
folium.Circle(
    location=[CHATEAU_LAT, CHATEAU_LON],
    radius=RAYON_MAX * 1000,  # En mètres
    color='blue',
    fill=True,
    fill_opacity=0.1
).add_to(m)

# Ajouter les clients
for _, client in df_clients.iterrows():
    folium.CircleMarker(
        location=[client['latitude'], client['longitude']],
        radius=4,
        color='green',
        fill=True,
        fill_opacity=0.7,
        popup=f"Client {int(client['id'])}: {int(client['nb_personnes'])} personnes<br>"
              f"Arrivée: {int(client['heure_arrivee'])//60}h{int(client['heure_arrivee'])%60:02d}<br>"
              f"Départ: {int(client['heure_depart'])//60}h{int(client['heure_depart'])%60:02d}"
    ).add_to(m)

# Sauvegarder la carte
m.save('./vrp/carte_clients_dinan.html')
print("Carte générée et sauvegardée dans 'carte_clients_dinan.html'")
