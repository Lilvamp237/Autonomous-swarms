import os
import sys
import traci
import math

# Set up SUMO paths
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.agents.graph_memory import SocialMemoryEngine

# Configuration
SUMO_CONFIG = "data/simulation.sumocfg"
SENSOR_RADIUS = 250.0  # 200-300m sensor range for vehicle detection
INTERACTION_LOG_INTERVAL = 10  # Log interactions every N steps to reduce DB load

# Neo4j Connection Details
DB_URI = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
DB_USER = os.environ.get("NEO4J_USER", "neo4j")
DB_PASS = os.environ.get("NEO4J_PASS", "Vehicles123")

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance between two positions."""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def detect_yielding(ego_id, target_id, ego_speed, target_speed, distance):
    """
    Heuristic to detect if ego vehicle yielded to target vehicle.
    Returns True if ego appears to have yielded (slowed down when close).
    """
    # Simple heuristic: if ego is slower than target and they're close
    if distance < 50.0 and ego_speed < target_speed and ego_speed < 5.0:
        return True
    return False

def run_simulation():
    """
    Main simulation loop with Neo4j Social Memory Engine integration.
    Detects vehicle interactions within sensor radius and logs to graph database.
    """
    print("Initializing Social Memory Engine...")
    memory = SocialMemoryEngine(uri=DB_URI, user=DB_USER, password=DB_PASS)
    
    print(f"Starting SUMO simulation with config: {SUMO_CONFIG}")
    traci.start(["sumo-gui", "-c", SUMO_CONFIG])
    
    step = 0
    interaction_cache = {}  # Track recently logged interactions to avoid spam
    
    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            vehicle_ids = traci.vehicle.getIDList()
            
            # Only process interactions every N steps for performance
            if step % INTERACTION_LOG_INTERVAL == 0 and len(vehicle_ids) > 0:
                print(f"\n=== Step {step}: Processing {len(vehicle_ids)} vehicles ===")
                
                # Process each vehicle and detect nearby interactions
                for ego_id in vehicle_ids:
                    try:
                        ego_pos = traci.vehicle.getPosition(ego_id)
                        ego_speed = traci.vehicle.getSpeed(ego_id)
                        
                        # Check all other vehicles for proximity
                        for target_id in vehicle_ids:
                            if target_id == ego_id:
                                continue
                            
                            target_pos = traci.vehicle.getPosition(target_id)
                            target_speed = traci.vehicle.getSpeed(target_id)
                            
                            # Calculate distance
                            distance = calculate_distance(ego_pos, target_pos)
                            
                            # If within sensor radius, log the interaction
                            if distance <= SENSOR_RADIUS:
                                # Check if this interaction was recently logged
                                interaction_key = f"{ego_id}-{target_id}-{step // INTERACTION_LOG_INTERVAL}"
                                
                                if interaction_key not in interaction_cache:
                                    # Detect yielding behavior
                                    yielded = detect_yielding(ego_id, target_id, 
                                                            ego_speed, target_speed, distance)
                                    
                                    # Create interaction data structure
                                    interaction_data = {
                                        "ego_id": ego_id,
                                        "target_id": target_id,
                                        "ego_svo_angle": 0.0,  # Placeholder - integrate with SVO module
                                        "target_svo_angle": 0.0,  # Placeholder - integrate with SVO module
                                        "distance": distance,
                                        "yielded": yielded
                                    }
                                    
                                    # Push to Neo4j
                                    memory.log_interaction(interaction_data)
                                    interaction_cache[interaction_key] = True
                                    
                                    if distance < 50.0:  # Only print close interactions
                                        print(f"  Close interaction: {ego_id} <-> {target_id} "
                                              f"(d={distance:.1f}m, yield={yielded})")
                    
                    except traci.exceptions.TraCIException as e:
                        print(f"  Warning: Could not process vehicle {ego_id}: {e}")
                        continue
                
                # Clean old entries from cache to prevent memory growth
                if len(interaction_cache) > 10000:
                    interaction_cache.clear()
            
            step += 1
            if step > 1000:  # Safety limit for testing
                print("\n=== Reached step limit (1000) ===")
                break
    
    except KeyboardInterrupt:
        print("\n=== Simulation interrupted by user ===")
    
    except Exception as e:
        print(f"\n=== ERROR: Simulation failed: {e} ===")
        raise
    
    finally:
        print("\nClosing SUMO simulation...")
        traci.close()
        print("Closing Neo4j connection...")
        memory.close()
        print("Simulation complete!")

if __name__ == "__main__":
    run_simulation()