#!/usr/bin/env python3
"""
Standalone verification that runner.py has been updated correctly.
Run this to verify the code changes were applied.
"""

import os

def check_runner_file():
    """Check if runner.py contains the logger integration."""
    
    runner_path = "src/simulation/runner.py"
    
    print("=" * 70)
    print("VERIFYING RUNNER.PY CHANGES")
    print("=" * 70)
    
    if not os.path.exists(runner_path):
        print(f"❌ File not found: {runner_path}")
        return False
    
    with open(runner_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("Logger import", "from src.metrics import logger"),
        ("Logger initialization", "logger.initialise_logger()"),
        ("Log tick call", "logger.log_tick("),
        ("Tick parameter", "tick = step,"),
        ("Swarm mode param", 'swarm_mode = "selfish",'),
        ("Delay metric", "intersection_delay_s = traci.simulation.getWaitingTime()"),
        ("Throughput metric", "throughput_vehicles = traci.simulation.getArrivedNumber()"),
        ("Collisions metric", "collisions = traci.simulation.getCollidingVehiclesNumber()"),
        ("Mean speed metric", "mean_speed_ms = sum("),
    ]
    
    results = []
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ {check_name:30s} → Found")
            results.append(True)
        else:
            print(f"❌ {check_name:30s} → NOT FOUND")
            results.append(False)
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ ALL CHECKS PASSED - runner.py is properly integrated!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Run: python test_runner_simulation.py")
        print("   (This simulates the logger without SUMO)")
        print("2. Run: python runner.py")
        print("   (This runs your full simulation with logging)")
        return True
    else:
        passed = sum(results)
        total = len(results)
        print(f"❌ {total - passed}/{total} checks failed")
        print("=" * 70)
        return False

if __name__ == "__main__":
    import sys
    success = check_runner_file()
    sys.exit(0 if success else 1)
