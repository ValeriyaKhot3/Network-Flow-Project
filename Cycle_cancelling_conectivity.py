import networkx as nx
from copy import deepcopy

def print_residual_graph_state(R, cycle=None):
    """
    Prints the state of the residual graph to the console for a given iteration.
    """
    print(f"\n========================================================")
    print(f"========================================================")
    
    # 1. Print cycle information if found
    if cycle:
        cycle_edges = []
        cycle_cost = 0
        for i in range(len(cycle) - 1):
            u = cycle[i]
            v = cycle[i + 1]
            # Use .get for safety, although the cycle should only contain existing edges
            weight = R[u][v].get("weight", 0)
            cycle_cost += weight
            cycle_edges.append(f"({u} -> {v})")
            
        print(f"Negative Cycle Found (Cost: {cycle_cost:.2f}): {' -> '.join(map(str, cycle[:-1]))} -> {cycle[0]}")
    else:
        print("No Negative Cycle Found. Termination condition met.")

    # 2. Print all residual edges
    print("\nResidual Edges (u -> v: Cap, Cost):")
    edges_to_print = []
    for u, v, data in R.edges(data=True):
        cap = data["capacity"]
        weight = data["weight"]
        # Highlight cycle edges in the printout
        if cycle:
            is_cycle_edge = False
            for i in range(len(cycle) - 1):
                if (u, v) == (cycle[i], cycle[i+1]):
                    is_cycle_edge = True
                    break
            
            label = f"   * {u} -> {v}: ({cap}, {weight})" if is_cycle_edge else f"     {u} -> {v}: ({cap}, {weight})"
        else:
            label = f"     {u} -> {v}: ({cap}, {weight})"
            
        edges_to_print.append(label)
        
    for label in sorted(edges_to_print):
         print(label)
    print(f"========================================================\n")

def cycle_cancelling(G, s, t, weight="weight",flow_func=None, capacity="capacity", negative_cycle_func=None):
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
    default_negative_cycle_func = nx.find_negative_cycle

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
        #the algorithm can run on negative too - think of delete it
        if data[weight] < 0:
            raise ValueError(f"Edge ({u},{v}) has negative weight ({data[weight]}).")
        
    if negative_cycle_func is None:
        negative_cycle_func = default_negative_cycle_func
    
    if not callable (negative_cycle_func):
        raise nx.NetworkXError("finding negative cycle func has to be callable.")

    # --------------------------------------------------------
    # 2. INITIAL MAX-FLOW (IGNORE COSTS)
    # --------------------------------------------------------
    
    # We temporarily build a capacity-only graph
    G_cap = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        G_cap.add_edge(u, v, capacity=data[capacity])

    max_flow_return = nx.maximum_flow(G_cap, s, t, flow_func=None)  # flow_dict is a nested dict
    flow_dict = max_flow_return[1]

    for u, v in G_cap.edges():
        # If node u has no outgoing flow dict, create one
        if u not in flow_dict:
            flow_dict[u] = {}

        # If edge (u, v) not assigned by max-flow, its flow is 0
        if v not in flow_dict[u]:
            flow_dict[u][v] = 0

    

    # --------------------------------------------------------
    # 3. BUILD INITIAL RESIDUAL GRAPH
    # --------------------------------------------------------
    
    def build_residual(G, flow):
        R = nx.DiGraph()
        for u, v, data in G.edges(data=True):
            cap = data[capacity]
            w = data[weight]

            f = flow.get(u, {}).get(v, 0)
            residual_fwd = cap - f
            residual_bwd = f

            # forward edge (u -> v)
            if residual_fwd > 0:
                R.add_edge(u, v, capacity=residual_fwd, weight=w)

            # backward edge (v -> u)
            if residual_bwd > 0:
                R.add_edge(v, u, capacity=residual_bwd, weight=-w)
        print("*************************\nThe residual: ")
        for u, v, data in G.edges(data=True):
            print(f"{u} -> {v} : cap = {data[capacity]} , w = {data[weight]}")

        print("*************************")

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
                flow.setdefault(u, {}).setdefault(v, 0)
                flow[u][v] += bottleneck

            elif G.has_edge(v, u):  
                # backward edge (v→u)
                flow.setdefault(v, {}).setdefault(u, 0)
                flow[v][u] -= bottleneck  # reduce forward flow

            else:
                raise RuntimeError("Cycle edge not found in original graph.")

    # --------------------------------------------------------
    # 4. MAIN LOOP — CANCEL NEGATIVE CYCLES
    # --------------------------------------------------------

    while True:
        R = build_residual(G, flow_dict)

        cycle_found = False  # will flip to True if we find & cancel a negative cycle

        # Iterate over strongly connected components of the residual graph
        for comp in nx.strongly_connected_components(R):
            # (optional) Skip trivial SCCs that cannot contain a cycle (no self-loop)
            if len(comp) == 1:
                u = next(iter(comp))
                if not R.has_edge(u, u):
                    continue

            # Induced subgraph on this SCC
            subR = R.subgraph(comp).copy()
            start = next(iter(comp))

            try:
                # Try to find a negative cycle inside this SCC
                cycle = negative_cycle_func(subR, start, weight="weight")

                print_residual_graph_state(R, cycle)
            except nx.NetworkXError:
                # No negative cycle reachable from this start node in this SCC
                continue

            # If we reach here, we found a negative cycle in this SCC.
            # Nodes/edges are the same as in R, so we use R for capacities.
            #print_residual_graph_state(R, cycle)

            # ---- your bottleneck & augment logic, now "per SCC" ----
            bottleneck = float("inf")
            for i in range(len(cycle) - 1):
                u = cycle[i]
                v = cycle[i + 1]
                cap = R[u][v]["capacity"]
                if cap < bottleneck:
                    bottleneck = cap

            if bottleneck <= 0:
                raise RuntimeError("Residual bottleneck is non-positive (should not happen).")

            augment_cycle(flow_dict, cycle, bottleneck)

            cycle_found = True
            # Important: break here and rebuild residual in the next outer iteration
            break

        if not cycle_found:
            # No negative cycle in any SCC ⇒ algorithm terminates
            #print_residual_graph_state(R, None)
            break


    # --------------------------------------------------------
    # 5. COMPUTE FINAL MINIMUM COST
    # --------------------------------------------------------

    min_cost = 0
    for u, nbrs in flow_dict.items():
        for v, f in nbrs.items():
            if f > 0:  # only forward flows
                min_cost += f * G[u][v][weight]

    return flow_dict, min_cost


