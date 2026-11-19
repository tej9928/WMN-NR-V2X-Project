#!/usr/bin/env bash
set -euo pipefail

# Locate the project repository
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

# Locate the ns-3 installation (sibling directory)
NS3_ROOT="$(cd -- "$PROJECT_ROOT/.." && pwd)"

# Experiment output directories (inside project repository)
EXPERIMENT_DIR="$PROJECT_ROOT/experiments/experiment_1"
DB_DIR="$EXPERIMENT_DIR/results/databases"
LOG_DIR="$EXPERIMENT_DIR/results/logs"

mkdir -p "$DB_DIR" "$LOG_DIR"

# Run ns-3 from its actual installation directory
cd "$NS3_ROOT"

if [[ ! -x "./ns3" ]]; then
    echo "Error: ns-3 launcher not found in $NS3_ROOT"
    exit 1
fi

# Experiment configuration
LANES=3
VEHICLES_PER_LANE=(5 9 13 17)
SEEDS=(1 2 3 4 5 6 7 8 9 10)

EXAMPLE="nr-v2x-west-to-east-highway"

COMMON_ARGS=(
    "--numLanes=${LANES}"
    "--enableOneTxPerLane=false"
    "--interVehicleDist=20"
    "--interLaneDist=4"
    "--enableSensing=false"
    "--slMaxTxTransNumPssch=5"
    "--saveDb=true"
)

for vehicles in "${VEHICLES_PER_LANE[@]}"; do

    total_ues=$((LANES * vehicles))

    echo "=========================================="
    echo "Vehicles per lane: $vehicles"
    echo "Total UEs: $total_ues"
    echo "=========================================="

    for seed in "${SEEDS[@]}"; do

        tag="density_v${vehicles}_seed${seed}"
        log_file="$LOG_DIR/${tag}.log"

        echo "Running: $tag"

        args=(
            "--numVehiclesPerLane=${vehicles}"
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
echo "All density simulations completed."
echo "Databases: $DB_DIR"
echo "Logs:      $LOG_DIR"
echo "=========================================="

