from src.data_loader import load_foot_traffic_data, load_atm_addresses
from src.feature_engineering import create_features
from src.grid_aggregation import aggregate_to_grid
from src.scoring_model import calculate_atm_score
from src.visualization import create_heatmap


def main():

    print("Loading traffic data...")
    gdf = load_foot_traffic_data("data/foot_traffic.csv")

    print("Loading ATM data...")
    atm_points = load_atm_addresses("data/atm_with_coordinates.csv")

    print("Creating features...")
    gdf = create_features(gdf)

    print("Aggregating to grid...")
    grid = aggregate_to_grid(gdf, grid_size=200)

    print("Filtering low traffic zones...")
    grid = grid[grid["total_traffic"] > 50].copy()

    print("Calculating ATM recommendations...")
    recommended_zones = calculate_atm_score(
        grid=grid,
        atm_points=atm_points,
        min_distance=300,
        top_n=10,
        mutual_exclusion_radius=400
    )

    print("Creating heatmap...")
    create_heatmap(
        full_grid=grid,                # ВСЯ карта
        recommended_zones=recommended_zones,  # только топ
        atm_points=atm_points
    )

    print("\nTop recommended locations:")
    print(recommended_zones[["atm_score", "total_traffic"]])

    print("\nDone!")


if __name__ == "__main__":
    main()
