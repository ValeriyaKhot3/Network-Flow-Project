import networkx as nx

def cycle_cancelling(G, s, t, weight="weight", capacity="capacity", negative_cycle_func=None):
    """
    Cycle-Cancelling algorithm for Min-Cost Max-Flow supporting opposite edges.
    """
    if negative_cycle_func is None:
        negative_cycle_func = nx.find_negative_cycle

    # 1. VALIDATION
    if not G.is_directed():
        raise TypeError("Input graph must be a directed graph.")

    # 2. INITIAL MAX-FLOW
    # We use a copy to ensure max_flow doesn't mutate original attributes
    flow_dict = nx.maximum_flow(G, s, t, capacity=capacity)[1]

    # 3. HELPER: BUILD MULTI-RESIDUAL GRAPH
    def build_residual(G, flow):
        # We use MultiDiGraph because u->v might have a forward residual edge 
        # AND a backward residual edge from the opposite original edge v->u.
        R = nx.MultiDiGraph()
        for u, v, data in G.edges(data=True):
            cap = data[capacity]
            w = data[weight]
            f = flow.get(u, {}).get(v, 0)

            # Forward residual edge: can push (cap - f) more flow at cost 'w'
            if f < cap:
                R.add_edge(u, v, weight=w, capacity=cap - f, type='fwd')
            
            # Backward residual edge: can push 'f' back at cost '-w'
            if f > 0:
                R.add_edge(v, u, weight=-w, capacity=f, type='bwd')
        return R

    # 4. HELPER: AUGMENT FLOW
    def augment_cycle(flow, cycle, R):
        bottleneck = float('inf')
        edges_in_cycle = []
        
        for i in range(len(cycle) - 1):
            u, v = cycle[i], cycle[i+1]
            edge_data = min(R[u][v].values(), key=lambda x: x['weight'])
            bottleneck = min(bottleneck, edge_data['capacity'])
            edges_in_cycle.append((u, v, edge_data))

        for u, v, data in edges_in_cycle:
            if data['type'] == 'fwd':
                flow[u][v] += bottleneck
            else:  # 'bwd'
                flow[v][u] -= bottleneck


    # 5. MAIN LOOP
    while True:
        R = build_residual(G, flow_dict)
        cycle_found = False

        for comp in nx.strongly_connected_components(R):
            if len(comp) < 2 and not R.has_edge(list(comp)[0], list(comp)[0]):
                continue
            
            subR = R.subgraph(comp)
            start_node = list(comp)[0]
            
            try:
                # nx.find_negative_cycle handles MultiDiGraph by using the min weight edge
                cycle = negative_cycle_func(subR, start_node, weight=weight)
                
                augment_cycle(flow_dict, cycle, R)
                cycle_found = True
                break # Rebuild residual after augmentation
            except nx.NetworkXError:
                continue

        if not cycle_found:
            break

    # 6. FINAL COST CALCULATION
    min_cost = sum(flow_dict[u][v] * G[u][v][weight] 
                   for u, v in G.edges() if flow_dict[u].get(v, 0) > 0)

    return flow_dict, min_cost