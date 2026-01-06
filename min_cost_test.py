import networkx as nx
from copy import deepcopy
import matplotlib.pyplot as plt
from build_graph_funcs import (
    build_and_draw_graph1,
    build_and_draw_graph2,
    build_and_draw_graph3,
    build_and_draw_graph4,
    build_and_draw_graph20,
)

def print_flow(flow_dict, total_cost):
    """
    Nicely print the flow per edge and the total cost.
    """
    print("Minimum-cost flow solution:")
    for u, nbrs in flow_dict.items():
        for v, f in nbrs.items():
            if f != 0:
                print(f"  {u} -> {v}: flow = {f}")
    print(f"\nTotal cost: {total_cost}")

def run_and_print_max_flow(G, name, s, t):
    """
    Helper to run maximum_flow on a graph and print the flow_value.
    """
    flow_value, flow_dict = nx.maximum_flow(G, s, t, capacity="capacity")
    print(f"\n{name}: max flow from {s} to {t} = {flow_value}")
    return flow_value, flow_dict

def run_and_print_min_cost_flow(G, name, s, t, amount):
    """
    Helper to run min_cost_flow on a graph:
    - Sets node demands to send `amount` units from s to t
    - Calls NetworkX's min_cost_flow
    - Prints the flow and its total cost
    """
    # 1. Set all node demands to 0
    nx.set_node_attributes(G, 0, "demand")

    # 2. Source supplies `amount`, sink consumes `amount`
    G.nodes[s]["demand"] = -amount
    G.nodes[t]["demand"] = amount

    # 3. Compute min-cost flow
    flow_dict = nx.min_cost_flow(
        G, demand="demand", capacity="capacity", weight="weight"
    )
    total_cost = nx.cost_of_flow(G, flow_dict, weight="weight")

    # 4. Print results
    print(f"\n{name}: min-cost flow from {s} to {t} with amount = {amount}")
    """
    for u, nbrs in flow_dict.items():
        for v, f in nbrs.items():
            if f != 0:
                print(f"  {u} -> {v}: flow = {f}")
    """
    print(f"  total cost = {total_cost}")

    return flow_dict, total_cost



if __name__ == "__main__":
    G1 = build_and_draw_graph1()
    G2 = build_and_draw_graph2()
    G3 = build_and_draw_graph3()
    G4 = build_and_draw_graph4()
    G20 = build_and_draw_graph20()

   # ---------- Max Flow ----------
    f1, _ = run_and_print_max_flow(G1, "Graph 1", 0, 5)
    f2, _ = run_and_print_max_flow(G2, "Graph 2", 0, 3)
    f3, _ = run_and_print_max_flow(G3, "Graph 3", 0, 6)
    f4, _ = run_and_print_max_flow(G4, "Graph 4", 0, 6)
    f20, _ = run_and_print_max_flow(G20, "Graph 20", 0, 19)

    # ---------- Min-Cost Flow (using the max-flow value as required amount) ----------
    run_and_print_min_cost_flow(G1, "Graph 1", 0, 5, f1)
    run_and_print_min_cost_flow(G2, "Graph 2", 0, 3, f2)
    run_and_print_min_cost_flow(G3, "Graph 3", 0, 6, f3)
    run_and_print_min_cost_flow(G4, "Graph 4", 0, 6, f4)
    run_and_print_min_cost_flow(G20, "Graph 20", 0, 19, f20)