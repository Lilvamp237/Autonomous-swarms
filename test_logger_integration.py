#!/usr/bin/env python3
"""
Quick test to verify logger integration works.
This simulates the logger calls without needing SUMO.
"""

from src.metrics import logger

# Test 1: Initialize logger
print("Test 1: Initializing logger...")
csv_path = logger.initialise_logger()
print(f"✅ Logger initialized at: {csv_path}\n")

# Test 2: Log some fake ticks
print("Test 2: Logging fake simulation ticks...")
for tick in range(5):
    logger.log_tick(
        tick                 = tick,
        swarm_mode           = "selfish",
        intersection_delay_s = 15.5 + tick * 0.5,
        throughput_vehicles  = tick * 3,
        collisions           = 1 if tick > 2 else 0,
        mean_speed_ms        = 10.0 - tick * 0.2
    )
    print(f"  ✅ Logged tick {tick}")

print(f"\n✅ All tests passed! Check 'data/metrics/simulation_log.csv' to verify CSV output.")
