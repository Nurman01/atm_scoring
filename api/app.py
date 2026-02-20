from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
import geopandas as gpd

from src.data_loader import load_foot_traffic_data, load_atm_addresses
from src.feature_engineering import create_features
from src.grid_aggregation import aggregate_to_grid
from src.scoring_model import calculate_atm_score


app = FastAPI(title="ATM Recommendation AI Service")


# --- CORS (чтобы Vue и Go могли обращаться) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ОСНОВНОЙ РАСЧЁТ (КЭШИРУЕТСЯ)
# ---------------------------------------------------------
@lru_cache(maxsize=1)
def compute_atm_model():
    print("AI MODEL: computing recommendations... (first call only)")

    # 1. Загрузка данных
    gdf = load_foot_traffic_data("data/foot_traffic.csv")
    atm_points = load_atm_addresses("data/atm_with_coordinates.csv")

    # 2. Фичи
    gdf = create_features(gdf)

    # 3. Сетка
    grid = aggregate_to_grid(gdf, grid_size=200)

    # 4. Убираем мусор
    grid = grid[grid["total_traffic"] > 50].copy()

    # 5. Рекомендации
    recommended = calculate_atm_score(
        grid=grid,
        atm_points=atm_points,
        min_distance=300,
        top_n=10,
        mutual_exclusion_radius=400
    )

    # -------------------------------------------------
    # PREPARE DATA FOR FRONTEND
    # -------------------------------------------------

    # WGS84
    grid = grid.to_crs(epsg=4326)
    recommended = recommended.to_crs(epsg=4326)
    atm_points = atm_points.to_crs(epsg=4326)

    # ---------------- HEATMAP (СЖАТИЕ ДАННЫХ) ----------------
    # берём только топ 25% по трафику
    threshold = grid["total_traffic"].quantile(0.75)
    heatmap = grid[grid["total_traffic"] >= threshold]

    grid_json = []
    for _, row in heatmap.iterrows():
        centroid = row.geometry.centroid
        grid_json.append({
            "lat": round(centroid.y, 6),
            "lon": round(centroid.x, 6),
            "weight": round(float(row["total_traffic"]), 2)
        })

    # ---------------- RECOMMENDED ----------------
    recommended_json = []
    for _, row in recommended.iterrows():
        centroid = row.geometry.centroid
        recommended_json.append({
            "lat": round(centroid.y, 6),
            "lon": round(centroid.x, 6),
            "score": round(float(row["atm_score"]), 3)
        })

    # ---------------- EXISTING ATM ----------------
    atm_json = []
    for _, row in atm_points.iterrows():
        atm_json.append({
            "lat": round(row.geometry.y, 6),
            "lon": round(row.geometry.x, 6),
            "address": row.get("full_address", "ATM")
        })

    print(f"Returned {len(grid_json)} heat points")
    print(f"Returned {len(recommended_json)} recommendations")

    return {
        "heatmap": grid_json,
        "recommended": recommended_json,
        "atm": atm_json
    }


# ---------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"service": "ATM AI service is running"}


@app.get("/recommend-atm")
def recommend_atm():
    return compute_atm_model()


# сброс кэша (удобно для обновления данных)
@app.post("/refresh")
def refresh_model():
    compute_atm_model.cache_clear()
    compute_atm_model()
    return {"status": "model recalculated"}
