import geopandas as gpd
import numpy as np
from shapely.geometry import box


def aggregate_to_grid(gdf: gpd.GeoDataFrame, grid_size: int = 200) -> gpd.GeoDataFrame:
    """
    Делит карту на сетку grid_size x grid_size (в метрах)
    и агрегирует трафик по ячейкам
    """

    xmin, ymin, xmax, ymax = gdf.total_bounds

    rows = int(np.ceil((ymax - ymin) / grid_size))
    cols = int(np.ceil((xmax - xmin) / grid_size))

    polygons = []

    for i in range(cols):
        for j in range(rows):
            x1 = xmin + i * grid_size
            y1 = ymin + j * grid_size
            x2 = x1 + grid_size
            y2 = y1 + grid_size
            polygons.append(box(x1, y1, x2, y2))

    grid = gpd.GeoDataFrame({"geometry": polygons}, crs=gdf.crs)

    # Spatial join
    joined = gpd.sjoin(gdf, grid, how="left", predicate="intersects")

    grid_agg = joined.groupby("index_right").agg({
        "total_traffic": "sum",
        "traffic_density": "mean"
    }).reset_index()

    grid = grid.merge(grid_agg, left_index=True, right_on="index_right")

    return grid
