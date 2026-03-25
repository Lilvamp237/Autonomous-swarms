"""
irl_estimator.py
Inverse Reinforcement Learning module for estimating the SVO angle (phi)
of a target vehicle by observing its driving behaviour over time.

Author: Person 3 - SVO Reasoning Module
Project: Autonomous Swarm Intersection Management
"""

import numpy as np


def estimate_phi_irl(
    ego_speeds: list,
    other_speeds: list,
    ego_distances: list
) -> float:
    """
    Estimate the SVO angle (phi) of a vehicle using a simplified IRL heuristic.

    phi = 0    means fully SELFISH  (cares only about itself)
    phi = π/2  means fully PROSOCIAL (cares equally about others)

    The function observes two behavioural features:
        1. Cooperation Ratio: how often did the ego slow down while others sped up?
        2. Gap Score: how large a gap did the ego maintain to its lead vehicle?

    Args:
        ego_speeds    (list): Speed of ego vehicle at each time tick in m/s
        other_speeds  (list): Mean speed of nearby vehicles at each tick in m/s
        ego_distances (list): Gap to lead vehicle at each tick in metres

    Returns:
        float: Estimated phi in radians, range [0, π/2]
    """
    # Convert all inputs to numpy arrays for vectorised math
    ego_speeds    = np.array(ego_speeds,    dtype=float)
    other_speeds  = np.array(other_speeds,  dtype=float)
    ego_distances = np.array(ego_distances, dtype=float)

    # Count ticks where ego decelerated — a sign of yielding behaviour
    decel_events = np.sum(np.diff(ego_speeds) < 0)

    # Divide by total transitions to get a ratio in [0, 1]
    # NOTE: 1e-9 added to prevent division by zero on single-element arrays
    cooperation_ratio = decel_events / (len(ego_speeds) - 1 + 1e-9)

    # Normalise mean gap against 50 m reference distance
    # A vehicle maintaining 50+ metres is considered fully courteous
    mean_gap  = np.mean(ego_distances)
    gap_score = np.clip(mean_gap / 50.0, 0.0, 1.0)

    # Combine features — cooperation weighted higher (0.6) than gap (0.4)
    # because active deceleration is a stronger prosocial signal than spacing
    prosociality = (0.6 * cooperation_ratio) + (0.4 * gap_score)

    # Scale prosociality score [0,1] linearly to phi range [0, π/2]
    return float(prosociality * (np.pi / 2))


if __name__ == "__main__":
    # Test with a vehicle that brakes repeatedly while others accelerate
    ego_sp  = [12.0, 10.0, 8.0, 6.0, 5.0, 7.0, 9.0]
    oth_sp  = [8.0,  9.0, 10.0, 11.0, 12.0, 11.0, 10.0]
    gaps    = [30.0, 28.0, 26.0, 35.0, 40.0, 38.0, 36.0]

    phi = estimate_phi_irl(ego_sp, oth_sp, gaps)
    print(f"Estimated phi = {phi:.4f} rad  ({np.degrees(phi):.2f}°)")
    print(f"Behaviour: {'Prosocial' if phi > np.pi / 4 else 'Selfish'}")