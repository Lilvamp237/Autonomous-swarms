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

# Sensor configuration (200-300m range)
SENSOR_RADIUS_MIN = 200.0  # meters
SENSOR_RADIUS_MAX = 300.0  # meters


def run_simulation():
    # Initialize Neo4j memory engine before starting the simulation
    memory = SocialMemoryEngine(DB_URI, DB_USER, DB_PASS)

    try:
        traci.start(["sumo-gui", "-c", SUMO_CONFIG])

        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            vehicle_ids = traci.vehicle.getIDList()

            # Set up context subscriptions for each vehicle (sensor data)
            # This tells TraCI to automatically track nearby vehicles within 300m
            for veh_id in vehicle_ids:
                traci.vehicle.subscribeContext(
                    veh_id, 
                    traci.constants.CMD_GET_VEHICLE_VARIABLE,
                    SENSOR_RADIUS_MAX,  # 300m radius
                    [traci.constants.VAR_POSITION, traci.constants.VAR_SPEED]
                )

            # Process interactions for each ego vehicle
            for ego_id in vehicle_ids:
                # Retrieve all vehicles within 300m radius of this ego vehicle
                context_results = traci.vehicle.getContextSubscriptionResults(ego_id)
                
                if context_results is None:
                    continue
                
                ego_pos = traci.vehicle.getPosition(ego_id)
                
                # Check each vehicle in sensor range
                for target_id, target_data in context_results.items():
                    # Skip self-interaction
                    if target_id == ego_id:
                        continue
                    
                    # Get target position from context data
                    target_pos = target_data.get(traci.constants.VAR_POSITION)
                    if target_pos is None:
                        continue
                    
                    # Calculate Euclidean distance
                    distance = math.sqrt(
                        (ego_pos[0] - target_pos[0]) ** 2 +
                        (ego_pos[1] - target_pos[1]) ** 2
                    )
                    
                    # Filter by sensor range (200-300m)
                    if SENSOR_RADIUS_MIN <= distance <= SENSOR_RADIUS_MAX:
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

    except Exception as e:
        print(f"Error during simulation: {e}")
        raise
    finally:
        traci.close()
        memory.close()


if __name__ == "__main__":
    run_simulation()
