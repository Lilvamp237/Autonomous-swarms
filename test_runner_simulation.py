#!/usr/bin/env python3
"""
Test script that simulates runner.py behavior WITHOUT needing SUMO.
This verifies the logger integration works correctly.

Usage: python test_runner_simulation.py
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.metrics import logger

def simulate_runner():
    """Simulate what runner.py does with the logger."""
    
    print("=" * 60)
    print("SIMULATING runner.py WITH LOGGER INTEGRATION")
    print("=" * 60)
    
    # Initialize logger (mimics line 34 in runner.py)
    print("\n[INIT] Initializing logger...")
    logger.initialise_logger()
    print("✅ Logger initialized")
    
    # Simulate 10 simulation steps
    print("\n[SIM] Running 10 simulated steps...\n")
    
    for step in range(10):
        # Simulate vehicle metrics (what SUMO would return)
        # In real runner.py, these come from TraCI calls:
        # - traci.simulation.getWaitingTime()
        # - traci.simulation.getArrivedNumber()
        # - traci.simulation.getCollidingVehiclesNumber()
        # - average of traci.vehicle.getSpeed()
        
        # Simulate gridlock building up (what happens with selfish agents)
        intersection_delay_s = 5.0 + (step ** 1.5)  # Growing delay
        throughput_vehicles = max(0, 10 - step)     # Fewer vehicles exiting
        collisions = 0 if step < 5 else step - 4    # Collisions start after step 5
        mean_speed_ms = 12.0 - (step * 0.8)         # Speed decreases
        
        # Call logger.log_tick (mimics lines 102-112 in runner.py)
        logger.log_tick(
            tick                 = step,
            swarm_mode           = "selfish",
            intersection_delay_s = intersection_delay_s,
            throughput_vehicles  = throughput_vehicles,
            collisions           = collisions,
            mean_speed_ms        = mean_speed_ms
        )
        
        print(f"  Step {step:2d}: delay={intersection_delay_s:6.2f}s, "
              f"throughput={throughput_vehicles:2d}, "
              f"collisions={collisions}, "
              f"speed={mean_speed_ms:5.2f}m/s")
    
    print("\n✅ Simulation complete!")
    
    # Verify CSV was created and populated
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    csv_path = "data/metrics/simulation_log.csv"
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        
        print(f"✅ CSV file created: {csv_path}")
        print(f"✅ Total rows: {len(lines)} (1 header + {len(lines)-1} data)")
        
        print("\n📄 CSV Content:")
        print("-" * 120)
        for i, line in enumerate(lines):
            if i == 0:
                print(f"[HEADER] {line.rstrip()}")
            else:
                print(f"[ROW {i:2d}] {line.rstrip()}")
        print("-" * 120)
        
        print("\n✅ Logger integration test PASSED!")
        return True
    else:
        print(f"❌ CSV file not created at {csv_path}")
        return False

if __name__ == "__main__":
    try:
        success = simulate_runner()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
