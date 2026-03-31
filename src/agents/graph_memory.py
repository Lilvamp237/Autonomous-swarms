from neo4j import GraphDatabase
import json

class SocialMemoryEngine:
    def __init__(self, uri, user, password):
        """Initialize the Neo4j connection with persistent session."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.session = self.driver.session()  # Persistent session for performance
        self._setup_constraints()

    def close(self):
        """Close the database connection and session."""
        try:
            if self.session:
                self.session.close()
        except Exception as e:
            print(f"Warning: Error closing session: {e}")
        finally:
            self.driver.close()

    def _setup_constraints(self):
        """Ensure vehicle IDs are unique in the graph."""
        query = """
        CREATE CONSTRAINT vehicle_id IF NOT EXISTS 
        FOR (v:Vehicle) REQUIRE v.id IS UNIQUE;
        """
        try:
            self.session.run(query)
            print("Graph constraints verified.")
        except Exception as e:
            print(f"Warning: Constraint setup issue (may already exist): {e}")

    def log_interaction(self, interaction_json):
        """
        Takes JSON data (e.g., Vehicle A yielded to Vehicle B) 
        and updates the graph database in real-time.
        Uses persistent session for better performance in simulation loops.
        """
        try:
            # Parse the JSON if it's a string, otherwise assume it's a dict
            data = json.loads(interaction_json) if isinstance(interaction_json, str) else interaction_json
            
            ego_id = data.get("ego_id")
            target_id = data.get("target_id")
            ego_svo = data.get("ego_svo_angle", 0.0)
            target_svo = data.get("target_svo_angle", 0.0)
            distance = data.get("distance", 0.0)
            yielded = 1 if data.get("yielded") else 0 # Convert boolean to int

            query = """
            // 1. Upsert Ego Vehicle
            MERGE (ego:Vehicle {id: $ego_id})
            ON CREATE SET ego.created_at = timestamp()
            SET ego.current_svo_angle = $ego_svo

            // 2. Upsert Target Vehicle
            MERGE (target:Vehicle {id: $target_id})
            ON CREATE SET target.created_at = timestamp()
            SET target.current_svo_angle = $target_svo

            // 3. Create or Update the Interaction Relationship
            MERGE (ego)-[r:INTERACTED_WITH]->(target)
            ON CREATE SET 
                r.first_seen = timestamp(), 
                r.yield_count = $yielded,
                r.interaction_count = 1
            ON MATCH SET 
                r.last_seen = timestamp(), 
                r.distance = $distance, 
                r.yield_count = r.yield_count + $yielded,
                r.interaction_count = r.interaction_count + 1
            """
            
            # Use persistent session instead of creating new one each time
            self.session.run(query, ego_id=ego_id, target_id=target_id, 
                            ego_svo=ego_svo, target_svo=target_svo, 
                            distance=distance, yielded=yielded)
            
            # Reduce logging verbosity for performance (can be removed in production)
            # print(f"Logged: {ego_id} -> {target_id} @ {distance}m")
            
        except Exception as e:
            print(f"Error logging interaction {ego_id} -> {target_id}: {e}")

    def get_historical_svo(self, ego_id):
        """
        Fetches the historical SVO behavior of vehicles the ego vehicle 
        has interacted with to inform the Nash Equilibrium math.
        """
        query = """
        MATCH (ego:Vehicle {id: $ego_id})-[r:INTERACTED_WITH]->(target:Vehicle)
        RETURN target.id AS target_id, 
               target.current_svo_angle AS svo_angle, 
               r.yield_count AS yields, 
               r.distance AS last_distance
        ORDER BY r.last_seen DESC 
        LIMIT 10
        """
        
        history = []
        with self.driver.session() as session:
            result = session.run(query, ego_id=ego_id)
            for record in result:
                history.append({
                    "target_id": record["target_id"],
                    "svo_angle": record["svo_angle"],
                    "yield_count": record["yields"],
                    "last_distance": record["last_distance"]
                })
        return history

#To test only
if __name__ == "__main__":
    # Neo4j desktop credentials
    DB_URI = "neo4j://localhost:7687"
    DB_USER = "neo4j"
    DB_PASS = "Vehicles123"

    # Initialize the memory engine
    memory = SocialMemoryEngine(DB_URI, DB_USER, DB_PASS)

    # 1. Create some dummy JSON data (Simulating TraCI output)
    dummy_interaction_1 = {
        "ego_id": "veh_001",
        "target_id": "veh_002",
        "ego_svo_angle": 0.5,       # Slightly prosocial
        "target_svo_angle": -0.2,   # Competitive
        "distance": 45.2,
        "yielded": True             # veh_001 yielded to veh_002
    }
    
    dummy_interaction_2 = {
        "ego_id": "veh_001",
        "target_id": "veh_003",
        "ego_svo_angle": 0.5,
        "target_svo_angle": 0.8,    # Highly prosocial
        "distance": 12.5,
        "yielded": False            # veh_001 did not yield to veh_003
    }

    # 2. Push the data to Neo4j
    memory.log_interaction(dummy_interaction_1)
    memory.log_interaction(dummy_interaction_2)

    # 3. Query the historical behavior for veh_001
    print("\n--- Fetching Memory for veh_001 ---")
    swarm_memory = memory.get_historical_svo("veh_001")
    for record in swarm_memory:
        print(record)

    # Close the connection
    memory.close()


# QUeries to check
# MATCH (n) RETURN n
# MATCH (n)-[r:INTERACTED_WITH]->(m) RETURN n, r, m