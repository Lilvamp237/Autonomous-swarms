import os
import sys
import math
import traci
import numpy as np
import random

# 1. Set up SUMO paths
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Import integrated modules
from src.agents.svo_agent import SVOAgent
from src.metrics.logger import initialise_logger, log_tick
from src.agents.graph_memory import SocialMemoryEngine

# Path to SUMO configuration
SUMO_CONFIG = "data/simulation.sumocfg"

# Neo4j connection settings
DB_URI  = "neo4j://localhost:7687"
DB_USER = "neo4j"
DB_PASS = "Vehicles123"

# Sensor configuration (200-300m range)
SENSOR_RADIUS_MIN = 10.0  # meters
SENSOR_RADIUS_MAX = 150.0  # meters


def run_simulation():
    """
    Main simulation loop integrating SVO agents, graph memory, and telemetry logging.
    
    Flow:
    1. Initialize database, logger, and agent dictionary
    2. Start SUMO simulation
    3. Each tick:
       - Track active vehicles and create SVOAgent instances
       - Detect vehicle interactions within sensor range
       - Execute game-theoretic Nash Equilibrium decisions
       - Log interactions to memory graph database
       - Extract system-wide metrics and log to CSV
    4. Cleanup database and SUMO connection
    """
    
    # ========== PRE-SIMULATION INITIALIZATION ==========
    
    # Initialize Neo4j memory engine
    memory = SocialMemoryEngine(DB_URI, DB_USER, DB_PASS)
    print("[Runner] Graph memory engine initialized")
    
    # Initialize telemetry CSV logger
    log_path = initialise_logger()
    print(f"[Runner] Telemetry logger initialized at: {log_path}")
    
    # Dictionary to track SVOAgent instances for all active vehicles
    active_agents = {}
    print("[Runner] Agent tracking dictionary created")

    try:
        # Start SUMO in GUI mode
        traci.start(["sumo-gui", "-c", SUMO_CONFIG])
        print("[Runner] SUMO simulation started")

        step = 0
        total_arrived_vehicles = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            # Execute one simulation step
            traci.simulationStep()

            # ========== AGENT TRACKING ==========
            
            # Fetch all active vehicle IDs in the current simulation
            vehicle_ids = traci.vehicle.getIDList()
            
            # Create SVOAgent instances for any new vehicles
            for veh_id in vehicle_ids:
                if veh_id not in active_agents:
                    # 1. Create the agent
                    new_agent = SVOAgent(veh_id)
                    
                    # 2. Randomly assign a personality (SVO Angle in degrees)
                    # 0.0 = Pure Selfish (Aggressive)
                    # 45.0 = Prosocial (Balanced)
                    # 90.0 = Pure Altruistic (Overly polite)
                    random_personality = random.choice([0.0, 45.0, 90.0])
                    new_agent.phi = random_personality 
                    #new_agent.phi = 0.0  # Force pure selfish behavior
                    
                    # 3. Add to the swarm
                    active_agents[veh_id] = new_agent
                    print(f"[Runner] New agent: {veh_id} | Assigned SVO: {random_personality}°")
            
            # Remove agents for vehicles that have exited the simulation
            exited_agents = [aid for aid in active_agents if aid not in vehicle_ids]
            for aid in exited_agents:
                del active_agents[aid]
                print(f"[Runner] Agent removed for exited vehicle: {aid}")

            # ========== GAME-THEORETIC INTERACTION LOGIC ==========
            
            # Set up context subscriptions for each vehicle (sensor data within 300m)
            for veh_id in vehicle_ids:
                traci.vehicle.subscribeContext(
                    veh_id,
                    traci.constants.CMD_GET_VEHICLE_VARIABLE,
                    SENSOR_RADIUS_MAX,  # 300m sensor radius
                    [traci.constants.VAR_POSITION, traci.constants.VAR_SPEED]
                )
            
            # Process interactions for each ego vehicle
            for ego_id in vehicle_ids:
                # Retrieve all vehicles within 300m radius
                context_results = traci.vehicle.getContextSubscriptionResults(ego_id)
                
                if context_results is None:
                    continue
                
                ego_pos = traci.vehicle.getPosition(ego_id)
                ego_speed = traci.vehicle.getSpeed(ego_id)
                
                # Iterate through vehicles in sensor range
                for target_id, target_data in context_results.items():
                    # Skip self-interaction
                    if target_id == ego_id:
                        continue
                    
                    # Get target position and speed
                    target_pos = target_data.get(traci.constants.VAR_POSITION)
                    target_speed = target_data.get(traci.constants.VAR_SPEED, 0.0)
                    
                    if target_pos is None:
                        continue
                    
                    # Calculate Euclidean distance
                    distance = math.sqrt(
                        (ego_pos[0] - target_pos[0]) ** 2 +
                        (ego_pos[1] - target_pos[1]) ** 2
                    )
                    
                    # Filter by sensor range (150m for intersection detection)
                    if distance <= SENSOR_RADIUS_MAX:
                        # Retrieve or create agents
                        ego_agent = active_agents[ego_id]
                        target_agent = active_agents[target_id]
                        
                        # ===== MOCK REWARDS BASED ON CURRENT SPEEDS =====
                        # R_self: reward of proceeding (proportional to current speed)
                        # R_others: reward others get if ego yields (delays averted)
                        
                        R_ego_self = ego_speed * 1.0            # Self-reward: maintain speed
                        R_ego_others = target_speed * 0.5       # Others-reward: help target keep moving
                        
                        R_target_self = target_speed * 1.0      # Target's self-reward
                        R_target_others = ego_speed * 0.5       # Target's others-reward
                        
                        # ===== COMPUTE UTILITIES FOR BOTH AGENTS =====
                        # Utility when yielding (lower self-reward, help others)
                        ego_utility_yield = ego_agent.compute_utility(
                            R_self=R_ego_self * 0.5,      # Reduced when yielding
                            R_others=R_ego_others * 1.5
                        )
                        ego_utility_proceed = ego_agent.compute_utility(
                            R_self=R_ego_self,
                            R_others=R_ego_others * 0.0   # No benefit to others if proceeding
                        )
                        
                        target_utility_yield = target_agent.compute_utility(
                            R_self=R_target_self * 0.5,
                            R_others=R_target_others * 1.5
                        )
                        target_utility_proceed = target_agent.compute_utility(
                            R_self=R_target_self,
                            R_others=R_target_others * 0.0
                        )
                        
                        # ===== NASH EQUILIBRIUM DECISION =====
                        # Evaluate the Bayesian Nash Equilibrium
                        nash_result = ego_agent.nash_decision(
                            utility_A_yield=ego_utility_yield,
                            utility_A_proceed=ego_utility_proceed,
                            utility_B_yield=target_utility_yield,
                            utility_B_proceed=target_utility_proceed
                        )
                        
                        # Extract decision: True if ego yields, False if ego proceeds
                        yielded = nash_result["vehicle_A_yields"]

                        # ===== ACTUALLY CONTROL THE PHYSICAL CAR =====
                        if yielded:
                            # Tell the car to brake to 0 m/s over the next 2 seconds
                            traci.vehicle.slowDown(ego_id, 5.0, 2.0)
                        else:
                            # Tell the car to proceed (hand control back to SUMO's default speed)
                            traci.vehicle.setSpeed(ego_id, -1.0)
                        
                        # ===== GRAPH MEMORY INTEGRATION =====
                        # Build interaction dictionary with real agent properties
                        interaction = {
                            "ego_id": ego_id,
                            "target_id": target_id,
                            "ego_svo_angle": float(ego_agent.phi),          # Real SVO angle
                            "target_svo_angle": float(target_agent.phi),    # Real SVO angle
                            "distance": round(distance, 4),
                            "yielded": bool(yielded),
                        }
                        
                        # Log interaction to graph database
                        memory.log_interaction(interaction)

            # ========== TELEMETRY EXTRACTION & LOGGING ==========
            
            # Extract system-wide metrics
            
            # Intersection delay: summed waiting time across intersection edges
            # (Adjust edge names to match your SUMO network)
            # ========== TELEMETRY EXTRACTION & LOGGING ==========
            
            # Extract system-wide metrics
            
            # 1. Cumulative Throughput (Add this initialization BEFORE the while loop starts!)
            # total_arrived_vehicles = 0  <-- Put this line near 'step = 0'
            
            total_arrived_vehicles += traci.simulation.getArrivedNumber()
            throughput_vehicles = total_arrived_vehicles
            
            # 2. Total Intersection Delay (Sum of all active vehicle wait times)
            if len(vehicle_ids) > 0:
                delays = [traci.vehicle.getAccumulatedWaitingTime(v) for v in vehicle_ids]
                intersection_delay_s = sum(delays)
            else:
                intersection_delay_s = 0.0
            
            # 3. Collisions: number of active vehicle collisions
            collisions = traci.simulation.getCollidingVehiclesNumber()
            
            # 4. Mean speed: average speed across all vehicles
            if len(vehicle_ids) > 0:
                speeds = [traci.vehicle.getSpeed(veh_id) for veh_id in vehicle_ids]
                mean_speed_ms = float(np.mean(speeds))
            else:
                mean_speed_ms = 0.0
            
            # Log all metrics to CSV
            log_tick(
                tick=step,
                swarm_mode="mixed_swarm",
                intersection_delay_s=intersection_delay_s,
                throughput_vehicles=throughput_vehicles,
                collisions=collisions,
                mean_speed_ms=mean_speed_ms,
                path=log_path
            )

            step += 1

    except Exception as e:
        print(f"[Runner] Simulation error: {e}")
        raise

    finally:
        # ========== CLEANUP ==========
        
        # Close graph database connection
        memory.close()
        print("[Runner] Graph memory connection closed")
        
        # Close SUMO TraCI connection
        traci.close()
        print("[Runner] SUMO connection closed")
        print(f"[Runner] Simulation complete. Total steps: {step}")
        print(f"[Runner] Telemetry saved to: {log_path}")


if __name__ == "__main__":
    run_simulation()