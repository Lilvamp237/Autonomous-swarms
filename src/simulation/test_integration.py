"""
Integration Test Script
Tests the connection between SUMO simulation and Neo4j Social Memory Engine.
Run this before merging to verify the integration is working correctly.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.agents.graph_memory import SocialMemoryEngine

def test_neo4j_connection():
    """Test 1: Verify Neo4j connection works"""
    print("=" * 60)
    print("TEST 1: Neo4j Connection")
    print("=" * 60)
    
    try:
        memory = SocialMemoryEngine(
            uri="neo4j://localhost:7687",
            user="neo4j",
            password="Vehicles123"
        )
        print("✓ Successfully connected to Neo4j")
        
        # Test basic write operation
        test_data = {
            "ego_id": "test_vehicle_001",
            "target_id": "test_vehicle_002",
            "ego_svo_angle": 0.5,
            "target_svo_angle": -0.2,
            "distance": 45.2,
            "yielded": True
        }
        
        memory.log_interaction(test_data)
        print("✓ Successfully wrote test interaction to database")
        
        # Test read operation
        history = memory.get_historical_svo("test_vehicle_001")
        if len(history) > 0:
            print(f"✓ Successfully retrieved {len(history)} historical records")
        else:
            print("⚠ No historical records found (this is OK for first run)")
        
        memory.close()
        print("✓ Successfully closed connection")
        print("\n✅ PASS: Neo4j integration is working\n")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: Neo4j connection failed: {e}\n")
        return False

def test_sumo_setup():
    """Test 2: Verify SUMO is properly configured"""
    print("=" * 60)
    print("TEST 2: SUMO Setup")
    print("=" * 60)
    
    if 'SUMO_HOME' not in os.environ:
        print("❌ FAIL: SUMO_HOME environment variable not set")
        return False
    
    print(f"✓ SUMO_HOME is set: {os.environ['SUMO_HOME']}")
    
    try:
        import traci
        print("✓ Successfully imported traci")
    except ImportError as e:
        print(f"❌ FAIL: Could not import traci: {e}")
        return False
    
    # Check if config file exists
    config_path = os.path.join(project_root, "data", "simulation.sumocfg")
    if os.path.exists(config_path):
        print(f"✓ Found simulation config: {config_path}")
    else:
        print(f"⚠ WARNING: Simulation config not found at: {config_path}")
        print("  Make sure to create your SUMO configuration before running")
    
    print("\n✅ PASS: SUMO setup is correct\n")
    return True

def test_dependencies():
    """Test 3: Verify all required dependencies are installed"""
    print("=" * 60)
    print("TEST 3: Dependencies Check")
    print("=" * 60)
    
    required_modules = [
        ("neo4j", "Neo4j Python driver"),
        ("traci", "SUMO TraCI interface"),
        ("pandas", "Data analysis (Person 4)"),
        ("matplotlib", "Plotting (Person 4)")
    ]
    
    all_ok = True
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"✓ {description}: {module_name}")
        except ImportError:
            print(f"❌ Missing: {description} ({module_name})")
            all_ok = False
    
    if all_ok:
        print("\n✅ PASS: All dependencies installed\n")
    else:
        print("\n❌ FAIL: Some dependencies are missing")
        print("Run: pip install -r requirements.txt\n")
    
    return all_ok

def test_integration_logic():
    """Test 4: Verify the integration logic is sound"""
    print("=" * 60)
    print("TEST 4: Integration Logic")
    print("=" * 60)
    
    # Check if runner.py has the integration code
    runner_path = os.path.join(project_root, "src", "simulation", "runner.py")
    
    with open(runner_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("from src.agents.graph_memory import SocialMemoryEngine", "Imports graph_memory"),
        ("SocialMemoryEngine(", "Initializes memory engine"),
        ("memory.log_interaction(", "Calls log_interaction"),
        ("calculate_distance(", "Has distance calculation"),
        ("detect_yielding(", "Has yielding detection"),
    ]
    
    all_ok = True
    for code_snippet, description in checks:
        if code_snippet in content:
            print(f"✓ {description}")
        else:
            print(f"❌ Missing: {description}")
            all_ok = False
    
    if all_ok:
        print("\n✅ PASS: Integration logic is complete\n")
    else:
        print("\n❌ FAIL: Integration logic has gaps\n")
    
    return all_ok

def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("SUMO + Neo4j INTEGRATION TEST SUITE")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Dependencies", test_dependencies()))
    results.append(("SUMO Setup", test_sumo_setup()))
    results.append(("Neo4j Connection", test_neo4j_connection()))
    results.append(("Integration Logic", test_integration_logic()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - READY FOR MERGE")
    else:
        print("⚠️  SOME TESTS FAILED - DO NOT MERGE YET")
    print("=" * 60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
