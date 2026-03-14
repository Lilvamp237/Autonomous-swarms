import os
import sys
import math
import traci

# 1. Set up SUMO paths
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

from src.agents.graph_memory import SocialMemoryEngine

# 2. Path to your config file
SUMO_CONFIG = "data/simulation.sumocfg"

# Neo4j connection settings
DB_URI  = "neo4j://localhost:7687"
DB_USER = "neo4j"
DB_PASS = "Vehicles123"


def run_simulation():
    # 3. Initialize Neo4j memory engine BEFORE starting TraCI
    memory = SocialMemoryEngine(DB_URI, DB_USER, DB_PASS)

    try:
        # Start SUMO in GUI mode
        traci.start(["sumo-gui", "-c", SUMO_CONFIG])

        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            # 4. Grab the list of currently active vehicles
            vehicle_ids = traci.vehicle.getIDList()

            # 5. Log an interaction whenever at least 2 vehicles are present
            if len(vehicle_ids) >= 2:
                ego_id    = vehicle_ids[0]
                target_id = vehicle_ids[1]

                # Calculate Euclidean distance between the two vehicles via TraCI
                ego_pos    = traci.vehicle.getPosition(ego_id)
                target_pos = traci.vehicle.getPosition(target_id)
                distance   = math.sqrt(
                    (ego_pos[0] - target_pos[0]) ** 2 +
                    (ego_pos[1] - target_pos[1]) ** 2
                )

                # 6. Dummy interaction dict — SVO math to be filled in by Person 3
                interaction = {
                    "ego_id":           ego_id,
                    "target_id":        target_id,
                    "ego_svo_angle":    0.5,    # placeholder
                    "target_svo_angle": -0.2,   # placeholder
                    "distance":         round(distance, 4),
                    "yielded":          True,   # placeholder
                }

                memory.log_interaction(interaction)

            step += 1
            if step > 1000:  # Stop after 1000 steps for the test
                break

    finally:
        # 7. Always close both TraCI and Neo4j connections on exit
        traci.close()
        memory.close()


if __name__ == "__main__":
    run_simulation()