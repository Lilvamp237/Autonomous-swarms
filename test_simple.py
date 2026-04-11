#!/usr/bin/env python3
"""
Minimal test to verify logger works without SUMO.
Run this manually with: python test_simple.py
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.metrics import logger
    print("✅ Successfully imported logger module")
except ImportError as e:
    print(f"❌ Failed to import logger: {e}")
    sys.exit(1)

# Test initialization
try:
    csv_path = logger.initialise_logger()
    print(f"✅ Logger initialized at: {csv_path}")
except Exception as e:
    print(f"❌ Failed to initialize logger: {e}")
    sys.exit(1)

# Test logging a tick
try:
    logger.log_tick(
        tick=0,
        swarm_mode="selfish",
        intersection_delay_s=12.5,
        throughput_vehicles=0,
        collisions=0,
        mean_speed_ms=11.2
    )
    print("✅ Successfully logged tick 0")
except Exception as e:
    print(f"❌ Failed to log tick: {e}")
    sys.exit(1)

# Log a few more ticks to populate CSV
try:
    for tick in range(1, 5):
        logger.log_tick(
            tick=tick,
            swarm_mode="selfish",
            intersection_delay_s=12.5 + tick * 0.3,
            throughput_vehicles=tick * 2,
            collisions=1 if tick > 2 else 0,
            mean_speed_ms=11.2 - tick * 0.1
        )
    print("✅ Logged 4 additional ticks (total 5 rows)")
except Exception as e:
    print(f"❌ Failed to log ticks: {e}")
    sys.exit(1)

# Verify the CSV was created
try:
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        print(f"✅ CSV file exists with {len(lines)} lines (1 header + {len(lines)-1} data rows)")
        print("\n📄 CSV Preview:")
        print("".join(lines[:3]))  # Print header and first 2 rows
    else:
        print(f"❌ CSV file not created at {csv_path}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Failed to verify CSV: {e}")
    sys.exit(1)

print("\n✅ All tests passed! Logger is working correctly.")
