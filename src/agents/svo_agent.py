"""
svo_agent.py
Core decision-making agent for each autonomous vehicle in the swarm.
Implements the SVO utility function, IRL-based phi estimation,
and a Nash Equilibrium solver for yield/proceed decisions at intersections.

Author: Person 3 - SVO Reasoning Module
Project: Autonomous Swarm Intersection Management
Depends: irl_estimator.py must be in the same directory
"""

import numpy as np
from .irl_estimator import estimate_phi_irl


class SVOAgent:
    """
    Represents a single autonomous vehicle with Social Value Orientation.

    Each agent holds a phi angle that describes its social disposition,
    and exposes methods to compute utility, update phi from observations,
    and resolve intersection conflicts via Nash Equilibrium.

    Attributes:
        vehicle_id (str):   Unique ID matching the SUMO/TraCI vehicle ID
        phi        (float): SVO angle in radians
                            0    = fully selfish
                            π/4  = balanced (default)
                            π/2  = fully prosocial
    """

    def __init__(self, vehicle_id: str, phi: float = None):
        """
        Initialise an SVOAgent for a given vehicle.

        Args:
            vehicle_id (str):   Unique vehicle identifier e.g. "flow_NS.0"
            phi        (float): Initial SVO angle in radians.
                                Defaults to π/4 (balanced) if not provided.
        """
        self.vehicle_id = vehicle_id

        # Default to π/4 if no phi is given — agent starts as balanced
        self.phi = phi if phi is not None else (np.pi / 4)

        print(f"[SVOAgent] '{self.vehicle_id}' initialised | phi={np.degrees(self.phi):.1f}°")

    def compute_utility(
        self,
        R_self: float,
        R_others: float,
        phi: float = None
    ) -> float:
        """
        Compute the SVO utility for a given action.

        Formula:
            U_i = R_self * cos(φ) + R_others * sin(φ)

        When phi = 0 (selfish):    U = R_self only  (ignores others)
        When phi = π/2 (prosocial): U = R_others only (ignores self)
        In between: a weighted blend of both rewards

        Args:
            R_self   (float): Reward the ego vehicle gains from this action
                              e.g. speed gain in m/s
            R_others (float): Total reward other vehicles gain from this action
                              e.g. seconds of delay saved for neighbours
            phi      (float): Override the agent's stored phi for this call.
                              If None, self.phi is used.

        Returns:
            float: Computed utility — higher means this action is more preferred
        """
        # Fall back to this agent's stored phi if none is passed in
        phi = phi if phi is not None else self.phi

        # Core SVO utility formula
        utility = (R_self * np.cos(phi)) + (R_others * np.sin(phi))

        return float(utility)

    def update_phi_from_behaviour(
        self,
        ego_speeds: list,
        other_speeds: list,
        distances: list
    ) -> float:
        """
        Observe this vehicle's recent driving behaviour and update phi via IRL.

        In the full system this is called every N ticks from runner.py using
        live TraCI speed and distance data. For now it works with any dummy arrays.

        Args:
            ego_speeds   (list): Speed history of this vehicle in m/s per tick
            other_speeds (list): Mean speed of nearby vehicles in m/s per tick
            distances    (list): Gap to lead vehicle in metres per tick

        Returns:
            float: The newly estimated phi (also stored in self.phi)
        """
        old_phi = self.phi

        # Delegate the IRL computation to irl_estimator.py
        self.phi = estimate_phi_irl(ego_speeds, other_speeds, distances)

        print(f"[SVOAgent] '{self.vehicle_id}' phi updated: "
              f"{np.degrees(old_phi):.1f}° → {np.degrees(self.phi):.1f}°")

        return self.phi

    def nash_decision(
        self,
        utility_A_yield: float,
        utility_A_proceed: float,
        utility_B_yield: float,
        utility_B_proceed: float
    ) -> dict:
        """
        Resolve a 2-vehicle intersection conflict using Nash Equilibrium.

        THE GAME:
            Two vehicles A and B arrive at the intersection simultaneously.
            Each must independently choose YIELD or PROCEED.

            Payoff matrix (A = row player, B = column player):
                             B Yields          B Proceeds
                A Yields    (uAy, uBy)         (uAy, uBp)
                A Proceeds  (uAp, uBy)         (uAp, uBp)

        BEST RESPONSE RULE:
            A yields   if  utility_A_yield >= utility_A_proceed
            B yields   if  utility_B_yield >= utility_B_proceed

        A pure Nash Equilibrium exists when both players are simultaneously
        playing their best response — neither can improve by switching alone.

        POSSIBLE OUTCOMES:
            A yields,  B proceeds  → stable NE, safe passage
            A proceeds, B yields   → stable NE, safe passage
            Both yield             → cooperative but watch for deadlock
            Both proceed           → collision risk, escalate to coordinator

        Args:
            utility_A_yield   (float): U_A when A yields
            utility_A_proceed (float): U_A when A proceeds
            utility_B_yield   (float): U_B when B yields
            utility_B_proceed (float): U_B when B proceeds

        Returns:
            dict: {
                'vehicle_A_yields' (bool): True if A should yield,
                'vehicle_B_yields' (bool): True if B should yield,
                'equilibrium_type' (str):  Human-readable outcome label
            }
        """
        # Determine each vehicle's best response independently
        a_yields = utility_A_yield >= utility_A_proceed
        b_yields = utility_B_yield >= utility_B_proceed

        # Classify the resulting equilibrium
        if a_yields and b_yields:
            eq_type = "Both yield — cooperative (monitor for deadlock)"
        elif not a_yields and not b_yields:
            eq_type = "Both proceed — COLLISION RISK (escalate to coordinator)"
        else:
            eq_type = "Asymmetric — stable Nash Equilibrium"

        result = {
            "vehicle_A_yields": bool(a_yields),
            "vehicle_B_yields": bool(b_yields),
            "equilibrium_type": eq_type
        }

        print(f"[NashSolver] A yields={a_yields} | B yields={b_yields} | {eq_type}")

        return result


if __name__ == "__main__":

    # Create two agents — A is mostly selfish, B is mostly prosocial
    agent_A = SVOAgent(vehicle_id="veh_A", phi=0.2)   # ~11° selfish
    agent_B = SVOAgent(vehicle_id="veh_B", phi=1.1)   # ~63° prosocial

    # Define reward values for each possible action
    # Yielding gives moderate self-reward but benefits others greatly
    # Proceeding gives high self-reward but zero benefit to others
    R_self_yield,    R_others_yield   = 5.0,  8.0
    R_self_proceed,  R_others_proceed = 10.0, 0.0

    # Compute utility for each action for each agent
    uA_yield   = agent_A.compute_utility(R_self_yield,   R_others_yield)
    uA_proceed = agent_A.compute_utility(R_self_proceed, R_others_proceed)
    uB_yield   = agent_B.compute_utility(R_self_yield,   R_others_yield)
    uB_proceed = agent_B.compute_utility(R_self_proceed, R_others_proceed)

    print(f"\nAgent A | yield={uA_yield:.3f}  proceed={uA_proceed:.3f}")
    print(f"Agent B | yield={uB_yield:.3f}  proceed={uB_proceed:.3f}")

    # Run the Nash solver
    print("\n-- Nash Decision --")
    decision = agent_A.nash_decision(uA_yield, uA_proceed, uB_yield, uB_proceed)
    print(f"Result: {decision}")

    # Test IRL phi update with dummy behavioural data
    print("\n-- IRL Phi Update --")
    ego_sp = [12.0, 10.0, 8.0, 6.0, 5.0, 7.0]
    oth_sp = [8.0,  9.0, 10.0, 11.0, 12.0, 11.0]
    gaps   = [30.0, 28.0, 26.0, 35.0, 40.0, 38.0]
    agent_A.update_phi_from_behaviour(ego_sp, oth_sp, gaps)