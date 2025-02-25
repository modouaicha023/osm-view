import pandas as pd
import folium

csv_path = './trajet.csv'

df = pd.read_csv(csv_path)


df = df[df['railway'] == 'level_crossing']

m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=12)

for _, row in df.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=row['name'] if pd.notna(row['name']) else 'No Name',
        icon=folium.Icon(color='blue')
    ).add_to(m)

map_file = 'carte_trajets_csv.html'
m.save(map_file)

print(f"Carte sauvegardée avec succès dans le fichier : {map_file}")
