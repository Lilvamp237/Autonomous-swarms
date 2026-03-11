import os
import sys
import traci

# 1. Set up SUMO paths
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# 2. Path to your config file
SUMO_CONFIG = "data/simulation.sumocfg"

def run_simulation():
    # Start SUMO in GUI mode
    traci.start(["sumo-gui", "-c", SUMO_CONFIG])
    
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # 3. Data Verification: Get list of all vehicle IDs
        vehicle_ids = traci.vehicle.getIDList()
        
        if len(vehicle_ids) > 0:
            # Get data for the first vehicle as a test
            test_veh = vehicle_ids[0]
            pos = traci.vehicle.getPosition(test_veh)
            speed = traci.vehicle.getSpeed(test_veh)
            print(f"Step {step}: Veh {test_veh} at X={pos[0]:.2f}, Y={pos[1]:.2f} Speed={speed:.2f}")
        
        step += 1
        if step > 1000: # Stop after 1000 steps for the test
            break

    traci.close()

if __name__ == "__main__":
    run_simulation()