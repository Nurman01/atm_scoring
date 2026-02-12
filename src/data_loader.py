import pandas as pd
import geopandas as gpd
from shapely import wkt
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def load_foot_traffic_data(filepath: str) -> gpd.GeoDataFrame:
    df = pd.read_csv(filepath)
    df["geometry"] = df["geometry"].apply(wkt.loads)

    gdf = gpd.GeoDataFrame(df, geometry="geometry")
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf

def load_atm_addresses(filepath: str) -> gpd.GeoDataFrame:
    """
    Загружает ATM из CSV.
    Если есть lat/lon → использует их.
    Если нет → геокодирует по full_address.
    """

    df = pd.read_csv(filepath, encoding="utf-8-sig")

    # Убираем дубликаты по full_address
    df = df.drop_duplicates(subset=["full_address"])

    # Если координаты уже есть
    if "lat" in df.columns and "lon" in df.columns:
        print("Using existing coordinates from CSV...")
        df = df.dropna(subset=["lat", "lon"])
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["lon"], df["lat"]),
            crs="EPSG:4326"
        )
        return gdf

    # Если только адреса есть
    elif "full_address" in df.columns:
        print("Geocoding ATM addresses...")
        geolocator = Nominatim(user_agent="atm_project")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        latitudes = []
        longitudes = []

        for address in df["full_address"]:
            location = geocode(str(address) + ", Kazakhstan")
            if location:
                latitudes.append(location.latitude)
                longitudes.append(location.longitude)
            else:
                latitudes.append(None)
                longitudes.append(None)

        df["lat"] = latitudes
        df["lon"] = longitudes

        df = df.dropna(subset=["lat", "lon"])

        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["lon"], df["lat"]),
            crs="EPSG:4326"
        )
        return gdf

    else:
        raise ValueError("CSV must contain either 'full_address' or 'lat'/'lon' columns.")

