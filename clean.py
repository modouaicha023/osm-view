import pandas as pd
import numpy as np
import folium

df = pd.read_csv('osm__senegal_dataset.csv', low_memory=False)

missing_values = df.isnull().sum()
print("Valeurs manquantes par colonne:", missing_values)

colonnes_utiles = ['osm_id', 'osm_type', 'highway', 'railway', 'public_transport', 
                   'amenity', 'name', 'longitude', 'latitude', 'geom_type']
df_clean = df[colonnes_utiles]

df_clean = df_clean.replace({np.nan: None})

points_pertinents = df_clean[
    (df_clean['public_transport'].notna()) | 
    (df_clean['highway'].notna()) | 
    (df_clean['railway'].notna()) |
    (df_clean['amenity'].notna())
]

print(f"Nombre de points après filtrage initial: {len(points_pertinents)}")

points_pertinents = points_pertinents.drop_duplicates(subset=['longitude', 'latitude'])
print(f"Nombre de points après suppression des doublons: {len(points_pertinents)}")

limite_lat = (12.3, 16.7)  # Du sud au nord
limite_lon = (-17.5, -11.4)

points_filtres = points_pertinents[
    (points_pertinents['latitude'] >= limite_lat[0]) & 
    (points_pertinents['latitude'] <= limite_lat[1]) &
    (points_pertinents['longitude'] >= limite_lon[0]) & 
    (points_pertinents['longitude'] <= limite_lon[1])
]

print(f"Nombre de points après filtrage géographique: {len(points_filtres)}")

points_filtres.to_csv('cleaned_dataset.csv', index=False)
print("Données nettoyées sauvegardées dans 'cleaned_dataset.csv'")