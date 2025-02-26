import pandas as pd
import json
import folium

# Charger les données GeoJSON
with open('dinan_osm_data.geojson', 'r') as f:
    data = json.load(f)

# Créer une liste pour stocker les données extraites
extracted_data = []

# Parcourir les features et extraire les informations pertinentes
for feature in data['features']:
    if 'highway' in feature['properties']:
        item = {
            'id': feature['id'],
            'highway': feature['properties']['highway'],
            'geometry_type': feature['geometry']['type']
        }
        
        # Extraire les coordonnées selon le type de géométrie
        if feature['geometry']['type'] == 'Point':
            item['lon'] = feature['geometry']['coordinates'][0]
            item['lat'] = feature['geometry']['coordinates'][1]
        elif feature['geometry']['type'] == 'Polygon':
            # Prendre le premier point du polygone
            item['lon'] = feature['geometry']['coordinates'][0][0][0]
            item['lat'] = feature['geometry']['coordinates'][0][0][1]
        elif feature['geometry']['type'] == 'MultiPolygon':
            # Prendre le premier point du premier polygone
            item['lon'] = feature['geometry']['coordinates'][0][0][0][0]
            item['lat'] = feature['geometry']['coordinates'][0][0][0][1]
        
        # Ajouter d'autres propriétés si nécessaires
        for key, value in feature['properties'].items():
            if key != 'highway':
                item[f'prop_{key}'] = value
                
        extracted_data.append(item)

# Créer le DataFrame à partir des données extraites
df_filtered = pd.DataFrame(extracted_data)

# Supprimer les lignes avec des coordonnées manquantes
df_filtered.dropna(subset=['lat', 'lon'], inplace=True)

# Afficher les premières lignes pour vérifier
print(df_filtered[['highway', 'lat', 'lon']].head())

# Visualisation des points d'intérêt sur une carte Folium
map_center = [48.4541, -2.0474]  # Coordonnées centrales de Dinan
map_viz = folium.Map(location=map_center, zoom_start=13)

# Ajouter les points d'intérêt à la carte
for idx, row in df_filtered.iterrows():
    popup_content = f"Type: {row['highway']}"
    folium.Marker(location=[row['lat'], row['lon']], popup=popup_content).add_to(map_viz)

# Sauvegarder la carte
map_viz.save("carte_dinan.html")

print(f"Carte générée avec {len(df_filtered)} éléments.")