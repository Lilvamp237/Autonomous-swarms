# Autonomous SVO Swarms

Dynamic Social Value Orientation (SVO) simulation for autonomous vehicle swarms in an urban intersection scenario.

This project combines:

- SUMO + TraCI for microscopic traffic simulation
- Agent-level SVO reasoning for yield/proceed decisions
- A Neo4j graph memory for interaction history
- CSV telemetry logging for quantitative analysis

The central idea is to evaluate how each agent's social preference angle $\phi$ influences collective traffic outcomes such as throughput, delay, and collision risk.

## Overview

At each simulation tick, the runner:

1. Tracks active vehicles in SUMO
2. Creates a corresponding `SVOAgent` for each new vehicle
3. Observes nearby vehicles within a sensor radius
4. Computes SVO utilities:

$$
U_i = R_{self}\cos(\phi) + R_{others}\sin(\phi)
$$

5. Resolves interaction outcomes with a 2-agent Nash decision
6. Applies vehicle control in TraCI (e.g., slow down vs proceed)
7. Logs metrics to CSV and interaction history to Neo4j

## Tech Stack

- Python 3.10+
- Eclipse SUMO 1.26+ (GUI mode used by default)
- TraCI Python client
- Neo4j (local instance)
- NumPy, Pandas, Matplotlib, Jupyter

## Project Structure

```text
.
|-- README.md
|-- requirements.txt
|-- runner.py                        # Main simulation entrypoint
|-- data/
|   |-- simulation.sumocfg           # SUMO config
|   |-- networks/
|   |   `-- urban_intersection.net.xml
|   |-- routes/
|   |   `-- mixed_svo_swarm.rou.xml
|   `-- metrics/
|       |-- simulation_log.csv
|       `-- simulation_log_selfish.csv
|-- notebooks/
|   |-- result_analysis.ipynb
|   `-- figures/
`-- src/
		|-- agents/
		|   |-- svo_agent.py             # SVO utility + Nash decision logic
		|   |-- irl_estimator.py         # Heuristic IRL phi estimation
		|   `-- graph_memory.py          # Neo4j persistence layer
		|-- metrics/
		|   |-- logger.py                # CSV telemetry writer
		|   `-- throughput.py            # Throughput helper functions
		`-- simulation/
				|-- runner.py                # Earlier/basic runner variant
				`-- traci_utils.py
```

## Prerequisites

1. Install Python 3.10 or newer.
2. Install SUMO and ensure `sumo-gui` is available.
3. Set environment variable `SUMO_HOME`.
4. Install and run Neo4j locally.

### Windows: Set `SUMO_HOME`

Adjust path to your SUMO install directory (example):

```powershell
setx SUMO_HOME "C:\Program Files (x86)\Eclipse\Sumo"
```

Restart your terminal after setting this variable.

## Installation

```bash
pip install -r requirements.txt
```

## Neo4j Setup

By default, the runner uses:

- URI: `neo4j://localhost:7687`
- Username: `neo4j`
- Password: `Vehicles123`

These values are currently hardcoded in `runner.py` and `src/simulation/runner.py`. Update them before running if your local credentials differ.

## How To Run

Run from the repository root:

```bash
python runner.py
```

What this does:

- Starts SUMO in GUI mode using `data/simulation.sumocfg`
- Simulates until no expected vehicles remain
- Logs per-tick telemetry to `data/metrics/simulation_log.csv`
- Writes vehicle interaction edges to Neo4j

## Data Outputs

### 1) CSV Telemetry

`data/metrics/simulation_log.csv` contains:

- `tick`: simulation step
- `timestamp`: UTC write time
- `swarm_mode`: run mode label
- `intersection_delay_s`: sum of accumulated waiting time
- `throughput_vehicles`: cumulative arrived vehicles
- `collisions`: active colliding vehicle count
- `mean_speed_ms`: average speed across active vehicles

### 2) Graph Memory (Neo4j)

Nodes:

- `(:Vehicle {id, current_svo_angle, ...})`

Relationships:

- `(ego)-[:INTERACTED_WITH {interaction_count, yield_count, distance, ...}]->(target)`

Quick query examples:

```cypher
MATCH (n) RETURN n LIMIT 25;
```

```cypher
MATCH (a:Vehicle)-[r:INTERACTED_WITH]->(b:Vehicle)
RETURN a.id, b.id, r.interaction_count, r.yield_count, r.distance
ORDER BY r.interaction_count DESC
LIMIT 25;
```

## Notebook Analysis

Use `notebooks/result_analysis.ipynb` to explore telemetry trends and generate visualizations from the CSV logs.

## Key Modules

- `runner.py`
	- Primary integrated simulation loop
	- Creates agents, computes interactions, applies control, logs outputs

- `src/agents/svo_agent.py`
	- Implements SVO utility computation
	- Contains Nash decision helper for pairwise conflict outcomes

- `src/agents/irl_estimator.py`
	- Provides heuristic phi estimation based on deceleration and spacing behavior

- `src/agents/graph_memory.py`
	- Maintains Neo4j session
	- Upserts vehicles and interaction relationships

- `src/metrics/logger.py`
	- Initializes and appends simulation telemetry CSV rows

## Current Assumptions and Limitations

- SVO initialization in `runner.py` currently chooses from `[0.0, 45.0, 90.0]` values and stores directly in `phi`. The utility function expects radians; if you intend strict mathematical consistency, convert degrees to radians before assignment.
- Rewards (`R_self`, `R_others`) are currently speed-derived heuristic placeholders.
- Simulation uses GUI mode (`sumo-gui`) by default.
- Some modules in `src/simulation/` are stubs or legacy variants and are not the primary entrypoint.

## Troubleshooting

### `Please declare environment variable 'SUMO_HOME'`

- Set `SUMO_HOME` and restart terminal/session.

### `traci` import or runtime errors

- Confirm SUMO tools and Python bindings are installed.
- Reinstall dependencies from `requirements.txt`.

### Neo4j connection/auth errors

- Verify local Neo4j service is running.
- Check URI/port/credentials in `runner.py`.

### Empty or missing metrics output

- Confirm the simulation actually runs to completion.
- Verify `data/metrics/` is writable.

## Development Notes

- Main runnable script: `runner.py`
- CSV logger path default: `data/metrics/simulation_log.csv`
- SUMO config: `data/simulation.sumocfg`

If you want this project to be production-ready, recommended next steps are:

1. Move DB credentials and run settings to environment variables.
2. Add a CLI (`argparse`) for route files, modes, and output paths.
3. Add tests for SVO utility and IRL estimator behavior.
4. Add reproducible experiment configs for selfish/prosocial/mixed baselines.