import sqlite3
import csv
import statistics
from pathlib import Path
import matplotlib.pyplot as plt

# Experiment configuration
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

RESULTS_DIR = (
    PROJECT_ROOT
    / "experiments"
    / "experiment_1_a"
    / "results"
    / "databases"
)

ANALYSIS_DIR = RESULTS_DIR.parent / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

INTER_VEHICLE_DISTANCES = [40, 30, 20, 15, 10]
DATABASE_SUFFIX = "-nr-v2x-west-to-east-highway.db"


def get_run_prr(db_path):
    """Return the average PRR across transmitters for one simulation run."""

    conn = sqlite3.connect(db_path)

    try:
        rows = conn.execute(
            "SELECT avrgPrr, numNieb FROM avrgPrr"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        raise ValueError(f"No PRR records found in {db_path}")

    prr_values = [row[0] * 100 for row in rows]
    neighbour_counts = [row[1] for row in rows]

    print(
        f"{db_path.name}: "
        f"{len(prr_values)} transmitters, "
        f"average neighbours = "
        f"{statistics.mean(neighbour_counts):.2f}"
    )

    return statistics.mean(prr_values)


def main():

    summary = []

    for distance in INTER_VEHICLE_DISTANCES:

        density = 1000 / distance

        pattern = f"ivd_{distance}m_seed*{DATABASE_SUFFIX}"
        databases = sorted(RESULTS_DIR.glob(pattern))

        run_means = []

        for db_path in databases:
            try:
                run_prr = get_run_prr(db_path)
                run_means.append(run_prr)

            except Exception as error:
                print(f"Skipping {db_path.name}: {error}")

        if not run_means:
            print(
                f"No valid runs for inter-vehicle "
                f"distance {distance} m"
            )
            continue

        mean_prr = statistics.mean(run_means)

        std_prr = (
            statistics.stdev(run_means)
            if len(run_means) > 1
            else 0.0
        )

        summary.append({
            "inter_vehicle_distance_m": distance,
            "density_vehicles_per_km_per_lane": density,
            "successful_runs": len(run_means),
            "mean_prr_percent": mean_prr,
            "std_prr_percent": std_prr
        })

        print(
            f"\nDistance: {distance} m "
            f"({density:.2f} vehicles/km/lane)"
        )
        print(f"Mean PRR: {mean_prr:.2f}%")
        print(f"Std Dev:  {std_prr:.2f}%")
        print(f"Runs:     {len(run_means)}")

    if not summary:
        print("No results available.")
        return

    # Save CSV summary
    csv_path = ANALYSIS_DIR / "density_prr_summary.csv"

    with open(csv_path, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=summary[0].keys()
        )
        writer.writeheader()
        writer.writerows(summary)

    # Sort by increasing spatial density
    summary.sort(
        key=lambda row: row["density_vehicles_per_km_per_lane"]
    )

    x = [
        row["density_vehicles_per_km_per_lane"]
        for row in summary
    ]

    y = [
        row["mean_prr_percent"]
        for row in summary
    ]

    errors = [
        row["std_prr_percent"]
        for row in summary
    ]

    # Plot density vs PRR
    plt.figure(figsize=(8, 5))

    plt.errorbar(
        x,
        y,
        yerr=errors,
        marker="o",
        capsize=5,
        linewidth=2
    )

    plt.xlabel("Vehicle Density (vehicles/km/lane)")
    plt.ylabel("Average PRR (%)")
    plt.title("Spatial Vehicle Density vs Packet Reception Ratio")

    plt.xticks(x)
    plt.ylim(67.5, 69.5)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plot_path = ANALYSIS_DIR / "density_vs_prr.png"

    plt.savefig(plot_path, dpi=300)
    plt.show()

    print(f"\nCSV saved to: {csv_path}")
    print(f"Plot saved to: {plot_path}")


if __name__ == "__main__":
    main()

