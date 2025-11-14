import networkx as nx
from copy import deepcopy

def cycle_cancelling(G, s, t, weight="weight", capacity="capacity"):
    """
    Cycle-Cancelling algorithm for Minimum-Cost Flow.
    
    Parameters:
        G : directed graph (DiGraph)
        s : source node
        t : target node
        weight : edge attribute for cost
        capacity : edge attribute for capacity
    
    Returns:
        (flow_dict, min_cost)
    """

    # --------------------------------------------------------
    # 1. PARAMETER VALIDATION
    # --------------------------------------------------------

    if not isinstance(G, nx.DiGraph):
        raise TypeError("Input graph must be a directed graph (DiGraph).")

    if s not in G.nodes:
        raise ValueError("Source node does not exist in graph.")

    if t not in G.nodes:
        raise ValueError("Target node does not exist in graph.")

    for u, v, data in G.edges(data=True):
        if capacity not in data:
            raise ValueError(f"Edge ({u},{v}) missing capacity attribute.")
        if data[capacity] < 0:
            raise ValueError(f"Edge ({u},{v}) has negative capacity.")

        if weight not in data:
            raise ValueError(f"Edge ({u},{v}) missing weight attribute.")
        if data[weight] < 0:
            raise ValueError(f"Edge ({u},{v}) has negative weight ({data[weight]}).")

    # --------------------------------------------------------
    # 2. INITIAL MAX-FLOW (IGNORE COSTS)
    # --------------------------------------------------------
    
    # We temporarily build a capacity-only graph
    G_cap = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        G_cap.add_edge(u, v, capacity=data[capacity])

    flow_dict = nx.maximum_flow(G_cap, s, t)[1]  # flow_dict is a nested dict

    # --------------------------------------------------------
    # 3. BUILD INITIAL RESIDUAL GRAPH
    # --------------------------------------------------------

    def build_residual(G, flow):
        R = nx.DiGraph()
        for u, v, data in G.edges(data=True):
            cap = data[capacity]
            w = data[weight]

            f = flow[u][v] if v in flow[u] else 0
            residual_fwd = cap - f
            residual_bwd = f

            # forward edge (u -> v)
            if residual_fwd > 0:
                R.add_edge(u, v, capacity=residual_fwd, weight=w)

            # backward edge (v -> u)
            if residual_bwd > 0:
                R.add_edge(v, u, capacity=residual_bwd, weight=-w)

        return R

    # --------------------------------------------------------
    # Helper: increase flow on edges of a cycle
    # --------------------------------------------------------

    def augment_cycle(flow, cycle, bottleneck):
        """Increase flow along cycle edges by bottleneck."""
        for i in range(len(cycle)-1):
            u = cycle[i]
            v = cycle[i+1]

            if G.has_edge(u, v):  
                # forward edge (u→v)
                flow[u][v] += bottleneck

            elif G.has_edge(v, u):  
                # backward edge (v→u)
                flow[v][u] -= bottleneck  # reduce forward flow

            else:
                raise RuntimeError("Cycle edge not found in original graph.")

    # --------------------------------------------------------
    # 4. MAIN LOOP — CANCEL NEGATIVE CYCLES
    # --------------------------------------------------------

    while True:
        R = build_residual(G, flow_dict)

        try:
            # pick any source node — residual graph may not be connected
            source_any = next(iter(R.nodes))
            cycle = nx.find_negative_cycle(R, source_any, weight="weight")

        except nx.NetworkXError:
            # no negative cycle — we are done
            break

        # cycle returned as [v0, v1, ..., vk, v0]
        # compute bottleneck = min residual capacity on cycle
        bottleneck = float("inf")
        for i in range(len(cycle)-1):
            u = cycle[i]
            v = cycle[i+1]
            cap = R[u][v]["capacity"]
            bottleneck = min(bottleneck, cap)

        if bottleneck <= 0:
            raise RuntimeError("Residual bottleneck is non-positive (should not happen).")

        augment_cycle(flow_dict, cycle, bottleneck)

    # --------------------------------------------------------
    # 5. COMPUTE FINAL MINIMUM COST
    # --------------------------------------------------------

    min_cost = 0
    for u, nbrs in flow_dict.items():
        for v, f in nbrs.items():
            if f > 0:  # only forward flows
                min_cost += f * G[u][v][weight]

    return flow_dict, min_cost
