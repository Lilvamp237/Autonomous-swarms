import os
import sys
import math
import traci

# Set up SUMO paths
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

from src.agents.graph_memory import SocialMemoryEngine

# SUMO config path (relative to project root)
SUMO_CONFIG = "data/simulation.sumocfg"

# Neo4j connection settings
DB_URI  = "neo4j://localhost:7687"
DB_USER = "neo4j"
DB_PASS = "Vehicles123"


def run_simulation():
    # Initialize Neo4j memory engine before starting the simulation
    memory = SocialMemoryEngine(DB_URI, DB_USER, DB_PASS)

    try:
        traci.start(["sumo-gui", "-c", SUMO_CONFIG])

        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            vehicle_ids = traci.vehicle.getIDList()

            if len(vehicle_ids) >= 2:
                ego_id    = vehicle_ids[0]
                target_id = vehicle_ids[1]

                # Calculate Euclidean distance between the two vehicles
                ego_pos    = traci.vehicle.getPosition(ego_id)
                target_pos = traci.vehicle.getPosition(target_id)
                distance   = math.sqrt(
                    (ego_pos[0] - target_pos[0]) ** 2 +
                    (ego_pos[1] - target_pos[1]) ** 2
                )

                # Dummy interaction data — SVO math to be added by Person 3
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
            if step > 1000:
                break

    finally:
        traci.close()
        memory.close()


if __name__ == "__main__":
    run_simulation()
