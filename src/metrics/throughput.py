"""
throughput.py
Utility functions for computing intersection throughput metrics.
Throughput measures how many vehicles successfully clear the intersection
per unit time — the primary performance indicator for swarm evaluation.

Author: Person 4 - Swarm Evaluation Module
Project: Autonomous Swarm Intersection Management
"""


def compute_throughput(
    arrived_this_tick: int,
    elapsed_seconds: float
) -> float:
    """
    Compute vehicle throughput rate in vehicles-per-minute.

    Formula:
        throughput = (arrived_this_tick / elapsed_seconds) * 60

    Vehicles-per-minute is the standard unit in traffic engineering.
    e.g. 30 vehicles/min means one car clears the intersection every 2 seconds.

    Args:
        arrived_this_tick (int):   Vehicles that completed their route this tick.
                                   Source: traci.simulation.getArrivedNumber()
        elapsed_seconds   (float): Total simulation time elapsed so far in seconds.
                                   Source: traci.simulation.getTime()

    Returns:
        float: Throughput in vehicles per minute.
               Returns 0.0 if elapsed_seconds is zero to avoid division by zero.
    """
    # Guard against division by zero at the very first simulation tick
    if elapsed_seconds <= 0:
        return 0.0

    # Convert per-second rate to per-minute for readability
    return float((arrived_this_tick / elapsed_seconds) * 60.0)


def compute_efficiency_ratio(
    prosocial_throughput: float,
    selfish_throughput: float
) -> float:
    """
    Compute how much more efficient the prosocial swarm is vs the selfish swarm.

    Formula:
        efficiency_ratio = prosocial_throughput / selfish_throughput

    Interpretation:
        ratio > 1.0  means prosocial swarm is better
        ratio = 1.25 means prosocial is 25% more efficient
        ratio < 1.0  means selfish swarm unexpectedly outperformed

    Args:
        prosocial_throughput (float): Throughput of the prosocial swarm (veh/min)
        selfish_throughput   (float): Throughput of the selfish swarm (veh/min)

    Returns:
        float: Efficiency ratio. Returns 0.0 if selfish_throughput is zero.
    """
    # Guard against division by zero if selfish swarm had no throughput
    if selfish_throughput <= 0:
        return 0.0

    return float(prosocial_throughput / selfish_throughput)


if __name__ == "__main__":

    # Test 1: 30 vehicles cleared in 60 seconds → should be 30 veh/min
    rate = compute_throughput(arrived_this_tick=30, elapsed_seconds=60.0)
    print(f"Throughput: {rate:.2f} vehicles/min")

    # Test 2: prosocial cleared 40 veh/min vs selfish 30 veh/min
    ratio = compute_efficiency_ratio(
        prosocial_throughput=40.0,
        selfish_throughput=30.0
    )
    print(f"Efficiency ratio: {ratio:.2f}")
    print(f"Prosocial is {((ratio - 1) * 100):.1f}% more efficient")

    # Test 3: edge case — zero elapsed time should return 0.0 safely
    rate_zero = compute_throughput(arrived_this_tick=10, elapsed_seconds=0)
    print(f"Zero time edge case: {rate_zero}")