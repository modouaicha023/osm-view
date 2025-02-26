import pandas as pd
import json
import folium

# Charger les données GeoJSON
with open('./mistral/dinan_osm_data.geojson', 'r') as f:
    data = json.load(f)

# Convertir en DataFrame
df = pd.json_normalize(data['features'])

# Filtrer les données pour ne garder que les routes et points d'intérêt pertinents
df_filtered = df[df['properties.highway'].notnull()]  # Garder seulement les routes

# Fonction pour extraire les coordonnées en fonction du type de géométrie
def extract_coordinates(geometry):
    if geometry['type'] == 'Point':
        return geometry['coordinates']
    elif geometry['type'] == 'Polygon':
        return geometry['coordinates'][0][0]  # Prendre le premier point du polygone
    elif geometry['type'] == 'MultiPolygon':
        return geometry['coordinates'][0][0][0]  # Prendre le premier point du premier polygone
    else:
        return None

# Extraire les coordonnées
df_filtered['lon'] = df_filtered['geometry.type'].apply(lambda x: extract_coordinates({'type': x, 'coordinates': df_filtered.loc[df_filtered['geometry.type'] == x, 'geometry.coordinates'].values[0]})[0] if extract_coordinates({'type': x, 'coordinates': df_filtered.loc[df_filtered['geometry.type'] == x, 'geometry.coordinates'].values[0]}) else None)
df_filtered['lat'] = df_filtered['geometry.type'].apply(lambda x: extract_coordinates({'type': x, 'coordinates': df_filtered.loc[df_filtered['geometry.type'] == x, 'geometry.coordinates'].values[0]})[1] if extract_coordinates({'type': x, 'coordinates': df_filtered.loc[df_filtered['geometry.type'] == x, 'geometry.coordinates'].values[0]}) else None)

# Afficher les premières lignes pour vérifier
print(df_filtered[['properties.highway', 'lat', 'lon']].head())

# Visualisation des points d'intérêt sur une carte Folium
map_viz = folium.Map(location=[48.4541, -2.0474], zoom_start=13)

# Ajouter les points d'intérêt à la carte
for idx, row in df_filtered.iterrows():
    if row['lat'] is not None and row['lon'] is not None:
        folium.Marker(location=[row['lat'], row['lon']], popup=row['properties.highway']).add_to(map_viz)

# Sauvegarder la carte
map_viz.save("./mistral/carte_dinan.html")
