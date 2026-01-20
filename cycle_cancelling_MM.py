import networkx as nx
from copy import deepcopy
import math

def find_minimum_mean_negative_cycle(G, source=None, weight="weight"):
    """
    Finds the minimum mean negative cycle using Karp's Algorithm.
    
    1. Preprocesses MultiDiGraphs to simple DiGraphs (keeping min weight).
    2. Uses Dynamic Programming to find shortest paths of exact lengths.
    3. Applies Karp's formula to find the minimum mean value.
    4. Traces back through DP layers to recover the exact cycle nodes.
    """
    
    # STEP 1: PREPROCESS -------------------------------------------------------
    # Cycle-cancelling residual graphs are MultiDiGraphs
    # Karp's DP requires a simple DiGraph where we use the cheapest edge
    if not isinstance(G, (nx.DiGraph, nx.MultiDiGraph)):
        raise TypeError("Karp requires a directed graph")
    
    if G.is_multigraph():
        S = nx.DiGraph()
        for u, v, data in G.edges(data=True):
            w = data.get(weight, 0)
            if S.has_edge(u, v):
                # Save only one edge per direction between two nodes
                # Choose the cheapest edge
                if w < S[u][v][weight]:
                    S[u][v][weight] = w
            else:
                S.add_edge(u, v, **{weight: w})
        G = S

    # Initialization for dynamic programming
    nodes = list(G.nodes())
    n = len(nodes)
    if n == 0:
        raise nx.NetworkXError("Empty graph")

    idx = {v: i for i, v in enumerate(nodes)}   # Index mapping: node → int
    
    # dp[k][v] = min cost of walk of length k ending at v
    dp = [[math.inf] * n for _ in range(n + 1)]
    # parent[k][v] = the node u that preceded v in a path of length k
    # Compute walks of length up to n: any cycle must repeat within n nodes
    parent = [[None] * n for _ in range(n + 1)]

    # Virtual source: initialize all nodes at distance 0
    # Allows detecting cycles anywhere in the graph
    for v in range(n):
        dp[0][v] = 0

    # STEP 2: DYNAMIC PROGRAMMING ----------------------------------------------
    # Calculate shortest paths for every length k from 1 to n
    for k in range(1, n + 1):
        # Iterate over all directed edges (u → v)
        for u, v, data in G.edges(data=True):
            w = data[weight]
            # Convert node labels to integer indices for DP table access
            ui, vi = idx[u], idx[v]
            # If extending the cheapest (k−1)-edge walk ending at u via edge u→v
            # yields a cheaper k-edge walk ending at v, update the DP value
            if dp[k - 1][ui] + w < dp[k][vi]:
                dp[k][vi] = dp[k - 1][ui] + w
                parent[k][vi] = u

    # STEP 3: KARP'S MIN-MAX FORMULA -------------------------------------------
    mu = math.inf       # Initialize the minimum mean cycle cost to infinity
    v_star = None       # Will store a node that lies on the minimum mean cycle

    # Iterate over every node to consider cycles ending at that node
    for v in range(n):
        if dp[n][v] == math.inf:
            # Skip nodes that are unreachable in a walk of length n
            continue
        
        # max_k [(dp[n][v] - dp[k][v]) / (n - k)]
        max_avg = -math.inf
        for k in range(n):
            if dp[k][v] != math.inf:
                avg = (dp[n][v] - dp[k][v]) / (n - k)
                if avg > max_avg:
                    max_avg = avg

        if max_avg < mu:
            mu = max_avg
            v_star = v

    # STEP 4: TERMINATION CHECK ------------------------------------------------
    # mu < 0 indicates a negative mean cycle exists
    # Use small epsilon to handle floating point precision issues
    if v_star is None or mu >= -1e-11:
        raise nx.NetworkXError("No negative mean cycle found")

    # STEP 5: ROBUST CYCLE RECONSTRUCTION --------------------------------------
    # We trace the path back from the n-th layer to find the repeated nodes
    curr = nodes[v_star]
    path = []
    for k in range(n, -1, -1):
        path.append(curr)
        curr = parent[k][idx[curr]]
        if curr is None: break 

    path.reverse()
    
    # Identify the actual cycle within the path (remove the "tail")
    seen = {}
    for i, node in enumerate(path):
        if node in seen:
            # Return cycle including the closing node for the backbone
            return path[seen[node] : i + 1]
        seen[node] = i

    raise nx.NetworkXError("Failed to reconstruct cycle")

def print_graph_with_flows(G, flow_dict, capacity_attr="capacity"):
    print("\n=== Graph with Flows ===")
    for u, v, data in G.edges(data=True):
        flow = flow_dict.get(u, {}).get(v, 0)
        cap = data.get(capacity_attr, "?")
        print(f"{u} -> {v} | flow = {flow} / capacity = {cap}")

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
            w = R[u][v].get("weight", 0)
            cycle_cost += w
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
    default_negative_cycle_func = find_minimum_mean_negative_cycle
    #default_negative_cycle_func = nx.find_negative_cycle

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
        # We use MultiDiGraph because u->v might have a forward residual edge 
        # AND a backward residual edge from the opposite original edge v->u.
        R = nx.DiGraph()
        for u, v, data in G.edges(data=True):
            cap = data[capacity]
            w = data[weight]
            f = flow.get(u, {}).get(v, 0)

            # Forward residual edge: can push (cap - f) more flow at cost 'w'
            # for negative cycle, we need only the bwd edge, otherwise we work with an edge without flow
            if f < cap:
                if R.has_edge(u, v):
                    if R[u][v]["type"] == "bwd":
                        continue
                else:
                    R.add_edge(u, v, weight=w, capacity=cap - f, type='fwd')
            
            # Backward residual edge: can push 'f' back at cost '-w'
            if f > 0:
                if R.has_edge(v, u):
                    if R[v][u]["type"] == "fwd":
                        R.remove_edge(v, u)
                R.add_edge(v, u, weight=-w, capacity=f, type='bwd')
                
        return R

    # --------------------------------------------------------
    # Helper: increase flow on edges of a cycle
    # --------------------------------------------------------

    def augment_cycle(flow, cycle, bottleneck):
        """Increase flow along cycle edges by bottleneck."""
        for i in range(len(cycle)-1):
            u = cycle[i]
            v = cycle[i+1]

            if G.has_edge(u, v) and R.has_edge(u,v) and R[u][v]["type"] == "fwd":  
                # forward edge (u→v)
                flow.setdefault(u, {}).setdefault(v, 0)
                flow[u][v] += bottleneck

            elif G.has_edge(v, u) and R.has_edge(u,v) and R[u][v]["type"] == "bwd":  
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

        try:
            # Try to find a negative cycle in graph R
            cycle = negative_cycle_func(R, s, weight="weight")
            """
            if cycle:
                cycle_edges = []
                cycle_cost = 0
                for i in range(len(cycle) - 1):
                    u = cycle[i]
                    v = cycle[i + 1]
                    # Use .get for safety, although the cycle should only contain existing edges
                    w = R[u][v].get("weight", 0)
                    cycle_cost += w
                    cycle_edges.append(f"({u} -> {v})")
        
                print(f"Negative Cycle Found (Cost: {cycle_cost:.2f}): {' -> '.join(map(str, cycle[:-1]))} -> {cycle[0]}")
                print(f"the cycle cost: {cycle_cost}")
                if cycle_cost >= 0 :
                    continue
            print_residual_graph_state(R, cycle)
            """
        except nx.NetworkXError:
                cycle = None

        if not cycle:
            break  # terminate
        
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

    # --------------------------------------------------------
    # 5. COMPUTE FINAL MINIMUM COST
    # --------------------------------------------------------
    min_cost = 0
    for u, nbrs in flow_dict.items():
        for v, f in nbrs.items():
            if f > 0:  # only forward flows
                min_cost += f * G[u][v][weight]

    return flow_dict, min_cost


