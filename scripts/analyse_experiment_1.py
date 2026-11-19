
import sqlite3
import csv
import statistics
from pathlib import Path
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

EXPERIMENT_DIR = PROJECT_ROOT / "experiments" / "experiment_1"

DB_DIR = EXPERIMENT_DIR / "results" / "databases"
ANALYSIS_DIR = EXPERIMENT_DIR / "analysis"
PLOT_DIR = EXPERIMENT_DIR / "results" / "plots"

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

LANES = 3
VEHICLES_PER_LANE = [5, 9, 13, 17]
DATABASE_SUFFIX = "-nr-v2x-west-to-east-highway.db"


def get_run_prr(db_path):
    """Calculate the average transmitter-level PRR for one run."""

    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        "SELECT avrgPrr, numNieb FROM avrgPrr"
    ).fetchall()

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

    for vehicles in VEHICLES_PER_LANE:

        pattern = (
            f"density_v{vehicles}_seed*"
            f"{DATABASE_SUFFIX}"
        )

        databases = sorted(DB_DIR.glob(pattern))
        run_means = []

        for db_path in databases:
            try:
                run_prr = get_run_prr(db_path)
                run_means.append(run_prr)

            except Exception as error:
                print(f"Skipping {db_path.name}: {error}")

        if not run_means:
            print(
                f"No valid runs for "
                f"{vehicles} vehicles per lane"
            )
            continue

        mean_prr = statistics.mean(run_means)

        std_prr = (
            statistics.stdev(run_means)
            if len(run_means) > 1 else 0.0
        )

        total_vehicles = LANES * vehicles

        summary.append({
            "vehicles_per_lane": vehicles,
            "total_vehicles": total_vehicles,
            "successful_runs": len(run_means),
            "mean_prr_percent": mean_prr,
            "std_prr_percent": std_prr
        })

        print(
            f"\n{total_vehicles} vehicles: "
            f"Mean PRR = {mean_prr:.2f}%, "
            f"Std Dev = {std_prr:.2f}%"
        )

    if not summary:
        print("No results available.")
        return

    # Save summary CSV
    csv_path = ANALYSIS_DIR / "density_prr_summary.csv"

    with open(csv_path, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=summary[0].keys()
        )
        writer.writeheader()
        writer.writerows(summary)

    # Plot density vs PRR
    x = [row["total_vehicles"] for row in summary]
    y = [row["mean_prr_percent"] for row in summary]
    errors = [row["std_prr_percent"] for row in summary]

    plt.figure(figsize=(8, 5))

    plt.errorbar(
        x, y,
        yerr=errors,
        marker="o",
        capsize=5,
        linewidth=2
    )

    plt.xlabel("Total Number of Vehicles")
    plt.ylabel("Average PRR (%)")
    plt.title("Vehicle Density vs Packet Reception Ratio")

    plt.xticks(x)
    plt.ylim(0, 105)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plot_path = PLOT_DIR / "density_vs_prr.png"

    plt.savefig(plot_path, dpi=300)
    plt.show()

    print(f"\nCSV saved to: {csv_path}")
    print(f"Plot saved to: {plot_path}")


if __name__ == "__main__":
    main()

