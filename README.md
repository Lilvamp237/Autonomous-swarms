# SVO Swarm Simulation

**Dynamic Social Value Orientation in Autonomous Vehicle Swarms: A Framework for Collective Urban Intelligence**

This repository contains the simulation environment and decentralized multi-agent reinforcement learning (MARL) architecture for modeling Social Value Orientation (SVO) in autonomous vehicle swarms. By integrating microscopic traffic simulation (SUMO) with a graph-based social memory engine (Neo4j), this project evaluates how dynamically shifting an agent's SVO angle ($\phi$) resolves system-wide social dilemmas in unsignalized urban intersections.

## 🛠 Tech Stack
* **Language:** Python 3.10
* **Simulation Environment:** Eclipse SUMO (Simulation of Urban MObility) & TraCI API
* **Database / State Engine:** Neo4j (Graph Database) & Cypher
* **Data Analysis:** Pandas, Matplotlib, Jupyter Notebooks

## 📂 Repository Structure
* `data/`: SUMO network layouts (`.net.xml`) and route demands (`.rou.xml`).
* `docs/`: Architecture diagrams and research paper drafts.
* `notebooks/`: Jupyter notebooks for telemetry analysis and result visualization.
* `src/agents/`: The cognitive brain. Contains the SVO reward logic, Inverse Reinforcement Learning (IRL) estimators, and the Neo4j graph memory module.
* `src/metrics/`: Telemetry loggers to extract intersection throughput and delay metrics.
* `src/simulation/`: The core TraCI execution loop and SUMO environment runners.

## 🚀 Installation & Setup

**1. Clone the repository:**
```bash
git clone [https://github.com/your-username/svo-swarm-simulation.git](https://github.com/your-username/svo-swarm-simulation.git)
cd svo-swarm-simulation