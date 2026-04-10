"""
logger.py
Telemetry logger for the SUMO simulation.
Accepts per-tick simulation metrics and appends them row-by-row to a CSV file.
This CSV is later consumed by result_analysis.ipynb for charting.

Author: Person 4 - Swarm Evaluation Module
Project: Autonomous Swarm Intersection Management

Usage from runner.py:
    import logger
    logger.initialise_logger()
    logger.log_tick(tick=step, swarm_mode="prosocial", ...)
"""

import csv
import os
from datetime import datetime, timezone


# Default output path — directories are created automatically if missing
DEFAULT_CSV_PATH = "data/metrics/simulation_log.csv"

# Column names must stay in sync with the row dict inside log_tick()
FIELDNAMES = [
    "tick",                  # Simulation step number
    "timestamp",             # Real-world UTC time this row was written
    "swarm_mode",            # "selfish" or "prosocial"
    "intersection_delay_s",  # Total waiting time at intersection edges (seconds)
    "throughput_vehicles",   # Vehicles that exited the intersection this tick
    "collisions",            # Active collision count reported by SUMO
    "mean_speed_ms"          # Mean speed of vehicles on intersection edge (m/s)
]


def initialise_logger(path: str = DEFAULT_CSV_PATH) -> str:
    """
    Create a fresh CSV file with the correct column headers.
    Call this ONCE at the start of each simulation run.
    Overwrites any existing file at the given path.

    Args:
        path (str): File path for the CSV. Directories are auto-created.

    Returns:
        str: Path to the created CSV file.
    """
    # Create parent directories if they don't exist yet
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Open in write mode to overwrite existing file and write only headers
    with open(path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()

    print(f"[Logger] CSV initialised at: {path}")
    return path


def log_tick(
    tick: int,
    swarm_mode: str,
    intersection_delay_s: float,
    throughput_vehicles: int,
    collisions: int,
    mean_speed_ms: float,
    path: str = DEFAULT_CSV_PATH
) -> None:
    """
    Append one row of metrics to the CSV for the current simulation tick.
    Call this once per simulation step inside the runner.py while loop.

    When wired to SUMO, call it like this from runner.py:
        log_tick(
            tick                 = step,
            swarm_mode           = "prosocial",
            intersection_delay_s = traci.edge.getWaitingTime("edge_N2C"),
            throughput_vehicles  = traci.simulation.getArrivedNumber(),
            collisions           = traci.simulation.getCollidingVehiclesNumber(),
            mean_speed_ms        = traci.edge.getLastStepMeanSpeed("edge_N2C")
        )

    Args:
        tick                 (int):   Current simulation step number
        swarm_mode           (str):   "selfish" or "prosocial"
        intersection_delay_s (float): Waiting time at the intersection in seconds
        throughput_vehicles  (int):   Vehicles that completed their route this tick
        collisions           (int):   Number of colliding vehicle pairs this tick
        mean_speed_ms        (float): Average vehicle speed on intersection edge (m/s)
        path                 (str):   CSV file to append to
    """
    row = {
        "tick":                 tick,
        "timestamp":            datetime.now(timezone.utc).isoformat(),
        "swarm_mode":           swarm_mode,
        "intersection_delay_s": round(intersection_delay_s, 4),
        "throughput_vehicles":  throughput_vehicles,
        "collisions":           collisions,
        "mean_speed_ms":        round(mean_speed_ms, 4)
    }

    # Open in append mode so each call adds a row without erasing previous data
    with open(path, "a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writerow(row)


if __name__ == "__main__":

    TEST_PATH = "data/metrics/test_log.csv"

    # Initialise a fresh CSV
    initialise_logger(TEST_PATH)

    # Simulate 5 fake ticks and log them to verify CSV output
    for tick in range(5):
        log_tick(
            tick                 = tick,
            swarm_mode           = "prosocial",
            intersection_delay_s = 12.5 + tick * 0.3,
            throughput_vehicles  = tick * 2,
            collisions           = 0,
            mean_speed_ms        = 11.2 - tick * 0.1,
            path                 = TEST_PATH
        )
        print(f"[Logger] Logged tick {tick}")

    print(f"\n✅ Done. Check '{TEST_PATH}' to verify the CSV output.")