import folium
import geopandas as gpd


def create_heatmap(full_grid: gpd.GeoDataFrame,
                   recommended_zones: gpd.GeoDataFrame,
                   atm_points: gpd.GeoDataFrame,
                   output_file="atm_heatmap.html"):

    if full_grid.empty:
        print("WARNING: Grid is empty.")
        return

    # Добавляем zone_id для heatmap
    full_grid = full_grid.reset_index(drop=True)
    full_grid["zone_id"] = full_grid.index

    # Центр карты
    full_grid_proj = full_grid.to_crs(epsg=32643)
    centroids = full_grid_proj.centroid
    centroids = gpd.GeoSeries(centroids, crs=32643).to_crs(epsg=4326)

    center_lat = centroids.y.mean()
    center_lon = centroids.x.mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # -----------------------------
    # Heatmap всей сетки
    # -----------------------------
    folium.Choropleth(
        geo_data=full_grid,
        data=full_grid,
        columns=["zone_id", "total_traffic"],
        key_on="feature.properties.zone_id",
        fill_color="YlOrRd",
        fill_opacity=0.6,
        line_opacity=0.1,
        legend_name="Total Foot Traffic"
    ).add_to(m)

    # -----------------------------
    # Рекомендованные зоны (красные)
    # -----------------------------
    for _, row in recommended_zones.iterrows():
        centroid = row.geometry.centroid
        centroid = gpd.GeoSeries([centroid], crs=recommended_zones.crs).to_crs(epsg=4326).iloc[0]

        folium.Marker(
            location=[centroid.y, centroid.x],
            popup=f"Score: {round(row['atm_score'], 3)}",
            icon=folium.Icon(color="red", icon="star"),
        ).add_to(m)

    # -----------------------------
    # Существующие ATM (синие)
    # -----------------------------
    for _, row in atm_points.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=row.get("full_address", "ATM"),
            icon=folium.Icon(color="blue", icon="ok-sign"),
        ).add_to(m)

    m.save(output_file)
    print(f"Map saved to {output_file}")
