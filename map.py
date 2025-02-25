import pandas as pd
import folium

points = pd.read_csv('cleaned_dataset.csv')
print(f"Nombre total de points dans le dataset : {len(points)}")

carte = folium.Map(location=[14.4733, -14.4678], zoom_start=7)

echantillon = points.head(1000) if len(points) > 1000 else points
print(f"Visualisation de {len(echantillon)} points sur la carte")

for idx, row in echantillon.iterrows():
    if pd.notna(row['latitude']) and pd.notna(row['longitude']):
        color = 'blue'  
        if pd.notna(row['public_transport']):
            color = 'red'  
        elif pd.notna(row['highway']):
            color = 'green'
        elif pd.notna(row['railway']):
            color = 'orange'
            
        popup_text = f"ID: {row['osm_id']}"
        if pd.notna(row['name']):
            popup_text += f"<br>Nom: {row['name']}"
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=popup_text
        ).add_to(carte)

carte.save('map.html')
