import geopandas as gpd
from sklearn.preprocessing import MinMaxScaler
from shapely.strtree import STRtree


def calculate_atm_score(
    grid: gpd.GeoDataFrame,
    atm_points: gpd.GeoDataFrame,
    min_distance: int = 300,
    top_n: int = 10,
    mutual_exclusion_radius: int = 400
) -> gpd.GeoDataFrame:
    """
    1. Считает score по трафику
    2. Исключает зоны рядом с существующими ATM (hard exclusion)
    3. Greedy-выбор top_n зон с взаимным исключением
    """

    if grid.empty:
        raise ValueError("Grid is empty before scoring.")

    if atm_points.empty:
        raise ValueError("ATM dataset is empty.")

    grid = grid.copy()

    # Удаляем служебные колонки если есть
    for col in ["index_right", "index_left"]:
        if col in grid.columns:
            grid = grid.drop(columns=[col])

    # -------------------------
    # 1. Нормализация
    # -------------------------
    scaler = MinMaxScaler()
    grid[["traffic_norm", "density_norm"]] = scaler.fit_transform(
        grid[["total_traffic", "traffic_density"]]
    )

    grid["atm_score"] = 0.7 * grid["traffic_norm"] + 0.3 * grid["density_norm"]

    # -------------------------
    # 2. Переход в метры
    # -------------------------
    grid = grid.to_crs(epsg=3857)
    atm_points = atm_points.to_crs(epsg=3857)

    # -------------------------
    # 3. STRtree (Shapely 2.x правильное использование)
    # -------------------------
    atm_geoms = list(atm_points.geometry)
    tree = STRtree(atm_geoms)

    nearest_distances = []

    for geom in grid.geometry:
        centroid = geom.centroid

        # В Shapely 2.x возвращается ИНДЕКС
        nearest_index = tree.nearest(centroid)

        nearest_geom = atm_geoms[nearest_index]

        distance = centroid.distance(nearest_geom)
        nearest_distances.append(distance)

    grid["nearest_atm_distance"] = nearest_distances

    # -------------------------
    # 4. Hard exclusion
    # -------------------------
    grid = grid[grid["nearest_atm_distance"] > min_distance].copy()

    if grid.empty:
        print("WARNING: No zones left after exclusion filtering.")
        return grid.to_crs(epsg=4326)

    # -------------------------
    # 5. Greedy selection
    # -------------------------
    grid = grid.sort_values("atm_score", ascending=False)

    selected_rows = []
    selected_centroids = []

    for _, row in grid.iterrows():

        centroid = row.geometry.centroid

        too_close = False
        for sel_centroid in selected_centroids:
            if centroid.distance(sel_centroid) < mutual_exclusion_radius:
                too_close = True
                break

        if not too_close:
            selected_rows.append(row)
            selected_centroids.append(centroid)

        if len(selected_rows) >= top_n:
            break

    result = gpd.GeoDataFrame(selected_rows, crs=grid.crs)

    # обратно в WGS84
    result = result.to_crs(epsg=4326)

    return result
