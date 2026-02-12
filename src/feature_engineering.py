import geopandas as gpd


def create_features(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Создает новые признаки:
    - total_traffic
    - segment_length
    - traffic_density
    """

    # Общий трафик
    gdf["total_traffic"] = (
        gdf["weekday_traffic"] +
        gdf["weekend_traffic"]
    )

    # Переводим в метры для расчета длины
    gdf = gdf.to_crs(epsg=3857)

    gdf["segment_length"] = gdf.geometry.length

    # Плотность трафика
    gdf["traffic_density"] = (
        gdf["total_traffic"] /
        (gdf["segment_length"] + 1)
    )

    return gdf
