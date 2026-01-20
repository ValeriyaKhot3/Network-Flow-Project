from copy import deepcopy
import networkx as nx
import random
from typing import Tuple, Optional

from build_graph_funcs import (
    build_and_draw_graph1,
    build_and_draw_graph2,
    build_and_draw_graph3,
    build_and_draw_graph4,
    build_and_draw_graph20,
)

#from cycle_cancelling_conectivity import cycle_cancelling
#from MultiR import cycle_cancelling
#from find_minimum_mean_negative_cycle import cycle_cancelling
from cycle_cancelling_MM import cycle_cancelling
#from superNodeR import cycle_cancelling

from min_cost_test import(
    print_flow,
    run_and_print_min_cost_flow,
    run_and_print_max_flow,
)

def _nonzero_edge_flows(flow_dict):
    """
    Convert nested flow_dict {u: {v: f}} into flat dict {(u,v): f} ignoring zero flows.
    """
    result = {}
    for u, nbrs in flow_dict.items():
        for v, f in nbrs.items():
            if f != 0:
                result[(u, v)] = f
    return result


def compare_flows(name, flow_nx, cost_nx, flow_cc, cost_cc):
    """
    Compare NetworkX min_cost_flow result with cycle-cancelling result.
    """
    print(f"\n=== Comparison for {name} ===")
    print(f"NetworkX min cost     : {cost_nx}")
    print(f"Cycle-cancelling cost : {cost_cc}")

    if cost_nx == cost_cc:
        print("→ Costs are EQUAL.")
    else:
        print("→ Costs DIFFER.")

    flows_nx = _nonzero_edge_flows(flow_nx)
    flows_cc = _nonzero_edge_flows(flow_cc)

    all_edges = sorted(set(flows_nx.keys()) | set(flows_cc.keys()))
    diffs = []

    for e in all_edges:
        f_nx = flows_nx.get(e, 0)
        f_cc = flows_cc.get(e, 0)
        if f_nx != f_cc:
            diffs.append((e, f_nx, f_cc))

    if not diffs:
        print("→ Flow dictionaries are IDENTICAL on all nonzero edges.")
    else:
        print("→ Flow dictionaries differ on the following edges:")
        for (u, v), f_nx, f_cc in diffs:
            print(f"  edge {u} -> {v}: NetworkX={f_nx}, CycleCancelling={f_cc}")


def run_experiment_for_graph(build_fn, name, s, t):
    """
    Build the graph, run:
    - max flow
    - NetworkX min_cost_flow
    - your cycle_cancelling algorithm
    then compare the results.
    """
    # Build (and draw) the base graph
    G_base = build_fn()
    """
    for u, v, data in G_base.edges(data=True):
        print(f"{u} -> {v} | cap={data['capacity']} weight={data['weight']}")
    """

    # 1. Max flow (on a copy, just in case)
    f_max, _ = run_and_print_max_flow(deepcopy(G_base), name, s, t)

    # 2. NetworkX min-cost flow (on a fresh copy)
    G_nx = deepcopy(G_base)
    flow_nx, cost_nx = run_and_print_min_cost_flow(G_nx, name, s, t, f_max)

    # 3. Cycle-cancelling (on a fresh copy)
    print(f"\n{name} [CycleCancelling]: running cycle-cancelling from {s} to {t}")
    try:
        G_cc = deepcopy(G_base)
        flow_cc, cost_cc = cycle_cancelling(
            G_cc,
            s,
            t,
            weight="weight",
            capacity="capacity",
        )

        print(f"{name} [CycleCancelling]: total cost = {cost_cc}")
        """
        print("Flow (u -> v: f):")
        for u, nbrs in flow_cc.items():
            for v, f in nbrs.items():
                if f != 0:
                    print(f"  {u} -> {v}: {f}")
        """

        # 4. Compare both methods
        compare_flows(name, flow_nx, cost_nx, flow_cc, cost_cc)

    except Exception as e:
        print(f"\n{name} [CycleCancelling]: ERROR while running cycle-cancelling.")
        print("This may be due to:")
        print("- a missing or incompatible nx.find_negative_cycle implementation, or")
        print("- a bug in the augmentation / residual-graph logic.")
        print(f"Error details: {e}")





def build_random_directed_graph(
    num_nodes: int = 20,
    density: float = 0.3,
    capacity_range: Tuple[int, int] = (1, 20),
    weight_range: Tuple[int, int] = (1, 10),
    *,
    ensure_path: bool = True,
    source: int = 0,
    target: Optional[int] = None,
    allow_self_loops: bool = False,
    seed: Optional[int] = None,
) -> nx.DiGraph:
    """
    Generate a random directed graph and assign random 'capacity' and 'weight'
    to every edge.

    - Topology: nx.gnp_random_graph(..., directed=True)
    - Attributes:
        edge['capacity'] in [capacity_range[0], capacity_range[1]]
        edge['weight']   in [weight_range[0], weight_range[1]]

    Options:
    - ensure_path: if True, guarantees there is at least one directed path
      from source to target by adding a simple chain if needed.
    """
    if num_nodes < 2:
        raise ValueError("num_nodes must be >= 2")
    if not (0.0 <= density <= 1.0):
        raise ValueError("density must be in [0.0, 1.0]")
    c_lo, c_hi = capacity_range
    w_lo, w_hi = weight_range
    if c_lo > c_hi:
        raise ValueError("capacity_range must be (low, high) with low <= high")
    if w_lo > w_hi:
        raise ValueError("weight_range must be (low, high) with low <= high")

    if target is None:
        target = num_nodes - 1
    if not (0 <= source < num_nodes) or not (0 <= target < num_nodes):
        raise ValueError("source/target must be valid node indices")
    if source == target:
        raise ValueError("source and target must be different nodes")

    rng = random.Random(seed)

    # 1) Create directed topology
    G = nx.gnp_random_graph(num_nodes, density, directed=True, seed=seed)
    G = nx.DiGraph(G)  # ensure simple DiGraph (no parallel edges)

    # Optionally remove self-loops
    if not allow_self_loops:
        G.remove_edges_from(nx.selfloop_edges(G))


    # 2) Ensure at least one path from source to target (optional but useful for flow tests)
    if ensure_path:
        if not nx.has_path(G, source, target):
            # Add a simple chain: source -> ... -> target using random intermediate nodes
            nodes = list(range(num_nodes))
            nodes.remove(source)
            nodes.remove(target)
            rng.shuffle(nodes)
            chain = [source] + nodes[: max(0, min(len(nodes), 3))] + [target]  # short chain
            for u, v in zip(chain, chain[1:]):
                G.add_edge(u, v)
    """   
    for u, v, data in G.edges(data=True):
        print(f"{u} -> {v} ")
    """


    # 4) Assign random capacity/weight to EVERY edge
    for u, v in G.edges():
        G[u][v]["capacity"] = rng.randint(c_lo, c_hi)
        G[u][v]["weight"] = rng.randint(w_lo, w_hi)

    return G

def main():
    """
    Main entry point for the script.
    ("Graph 1", build_and_draw_graph1, 0, 5),
        ("Graph 2", build_and_draw_graph2, 0, 3),
        ("Graph 3", build_and_draw_graph3, 0, 6),
        ("Graph 4", build_and_draw_graph4, 0, 6),
        ("Graph 20", build_and_draw_graph20, 0, 19),
    """

    graph_configs = [
        ("Graph 100", lambda: build_random_directed_graph(
                                num_nodes=100,
                                density=0.8,
                                capacity_range=(1, 25),
                                weight_range=(1, 8),
                                ensure_path=True,
                                source=0,
                                target=99,
                                seed=16,
                            ),0,99)
    ]

    for name, build_fn, s, t in graph_configs:
        run_experiment_for_graph(build_fn, name, s, t)


if __name__ == "__main__":
    main()
