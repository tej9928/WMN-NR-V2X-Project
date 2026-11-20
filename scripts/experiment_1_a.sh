#!/usr/bin/env bash
set -euo pipefail

# Define the directories as they are present in the repo
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
NS3_ROOT="$(cd -- "$PROJECT_ROOT/.." && pwd)"

EXPERIMENT_DIR="$PROJECT_ROOT/experiments/experiment_1_a"
DB_DIR="$EXPERIMENT_DIR/results/databases"
LOG_DIR="$EXPERIMENT_DIR/results/logs"

mkdir -p "$DB_DIR" "$LOG_DIR"

cd "$NS3_ROOT"

# Experiment configuration
LANES=3
VEHICLES_PER_LANE=5

# This experiment aims at targeting a more precise notion of "vehicle density" by varying the interVehicleDist param
INTER_VEHICLE_DISTANCES=(40 30 20 15 10)

INTER_LANE_DIST=4
SEEDS=(1 2 3 4 5 6 7 8 9 10)

# We will be using the pre-existing highway example for our experiment changing only the command line parameters as needed.
EXAMPLE="nr-v2x-west-to-east-highway"

# We keep all other simulation parameters identical to experiment 1
COMMON_ARGS=(
    "--numLanes=${LANES}"
    "--numVehiclesPerLane=${VEHICLES_PER_LANE}"
    "--enableOneTxPerLane=false"
    "--interLaneDist=${INTER_LANE_DIST}"
    "--enableSensing=false"
    "--slMaxTxTransNumPssch=5"
    "--saveDb=true"
)

for distance in "${INTER_VEHICLE_DISTANCES[@]}"; do

    density=$(awk "BEGIN {printf \"%.2f\", 1000 / $distance}")
    total_ues=$((LANES * VEHICLES_PER_LANE))

    echo "=========================================="
    echo "Inter-vehicle distance: ${distance} m"
    echo "Density per lane: ${density} vehicles/km"
    echo "Total UEs: ${total_ues}"
    echo "=========================================="

    for seed in "${SEEDS[@]}"; do

        tag="ivd_${distance}m_seed${seed}"
        log_file="$LOG_DIR/${tag}.log"

        echo "Running: $tag"

        args=(
            "--interVehicleDist=${distance}"
            "--simTag=${tag}"
            "--outputDir=${DB_DIR}/"
            "--RngRun=${seed}"
            "${COMMON_ARGS[@]}"
        )

        printf -v args_string '%s ' "${args[@]}"

        if ./ns3 run "$EXAMPLE ${args_string}" > "$log_file" 2>&1; then
            echo "Completed: $tag"
        else
            echo "FAILED: $tag"
            echo "Check log: $log_file"
            exit 1
        fi

    done
done

echo "=========================================="
echo "All Experiment 1A simulations completed."
echo "Databases: $DB_DIR"
echo "Logs:      $LOG_DIR"
echo "=========================================="

