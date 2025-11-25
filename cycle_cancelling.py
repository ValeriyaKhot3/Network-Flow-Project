import networkx as nx
from copy import deepcopy
import matplotlib.pyplot as plt

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

    flow_dict = nx.maximum_flow(G_cap, s, t, flow_func=None)[1]  # flow_dict is a nested dict

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
            cycle = negative_cycle_func(R, source_any, weight="weight")
            print_residual_graph_state(R, cycle)

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



def build_and_draw_graph1():
    """
    Initializes a directed graph, adds edges with capacity and weight attributes,
    and visualizes the graph using fixed positions for layout.
    """
    # 1. Initialize a directed graph
    G = nx.DiGraph()

    # 2. Define the edges with (capacity, weight) attributes
    # Edges are defined as (source, target, {'capacity': c, 'weight': w})
    edges_with_attributes = [
        (0, 1, {'capacity': 10, 'weight': 1}),
        (1, 3, {'capacity': 5, 'weight': 1}),
        (1, 2, {'capacity': 10, 'weight': 1}),
        (3, 6, {'capacity': 10, 'weight': 1}),
        (3, 4, {'capacity': 5, 'weight': 3}),
        (6, 4, {'capacity': 10, 'weight': 1}),
        (2, 6, {'capacity': 10, 'weight': 1}),
        (2, 4, {'capacity': 7, 'weight': 4}),
        (4, 5, {'capacity': 15, 'weight': 1}),
    ]

    # 3. Add all edges and their attributes to the graph
    G.add_edges_from(edges_with_attributes)

    # 4. Define node positions to match the visual layout in the image
    pos = {
        0: (-3.0, 0.0),
        1: (-1.5, 0.0),
        2: (0.0, -1.5),
        3: (0.0, 1.5),
        4: (1.5, 0.0),
        5: (3.0, 0.0),
        6: (0.0, 0.0), # Central node
    }

    # 5. Extract edge labels for drawing
    # The label will be formatted as "(capacity, weight)"
    edge_labels = {
        (u, v): f"({d['capacity']},{d['weight']})"
        for u, v, d in G.edges(data=True)
    }

    # 6. Visualization settings
    plt.figure(figsize=(10, 6))

    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="#89CFF0", edgecolors="black", linewidths=1.5)

    # Draw the edges
    nx.draw_networkx_edges(G, pos, arrowsize=20, edge_color="black", width=2)

    # Draw node labels (the node numbers)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

    # Draw edge labels (the capacity and weight)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='black', label_pos=0.5, font_size=10)

    plt.title("Directed Graph with Capacity and Weight Attributes (NetworkX)")
    plt.axis('off') # Hide the axes
    plt.show()

    # Optional: Print graph information to verify
    print("Nodes in the graph:", G.nodes)
    print("Edges in the graph (u, v, data):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v}: Capacity={data['capacity']}, Weight={data['weight']}")
    return G

def build_and_draw_graph2():
    """
    Initializes the new 4-node directed graph, adds edges with capacity and weight attributes,
    and visualizes the graph using fixed positions for layout.
    
    Returns:
        nx.DiGraph: The constructed graph G.
    """
    # 1. Initialize a directed graph
    G = nx.DiGraph()

    # 2. Define the edges with (capacity, weight) attributes from the new image
    # Edges are defined as (source, target, {'capacity': c, 'weight': w})
    edges_with_attributes = [
        (0, 1, {'capacity': 2, 'weight': 1}),
        (0, 2, {'capacity': 4, 'weight': 1}),
        (1, 2, {'capacity': 3, 'weight': 1}),
        (1, 3, {'capacity': 1, 'weight': 4}),
        (2, 3, {'capacity': 6, 'weight': 1}),
    ]

    # 3. Add all edges and their attributes to the graph
    G.add_edges_from(edges_with_attributes)

    # 4. Define node positions to match the visual layout in the image
    pos = {
        0: (-2.0, 0.0), # Left
        1: (0.0, 1.0),  # Top middle
        2: (0.0, -1.0), # Bottom middle
        3: (2.0, 0.0),  # Right
    }

    # 5. Extract edge labels for drawing
    # The label will be formatted as "(capacity, weight)"
    edge_labels = {
        (u, v): f"({d['capacity']},{d['weight']})"
        for u, v, d in G.edges(data=True)
    }

    # 6. Visualization settings
    plt.figure(figsize=(8, 5))

    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="#89CFF0", edgecolors="black", linewidths=1.5)

    # Draw the edges
    nx.draw_networkx_edges(G, pos, arrowsize=20, edge_color="black", width=2)

    # Draw node labels (the node numbers)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

    # Draw edge labels (the capacity and weight)
    # label_pos=0.3 is used for edge 1->2 to avoid overlap with node 6
    edge_label_pos = {p: 0.5 for p in pos}
    edge_label_pos[(1, 2)] = 0.3 # Move label for 1->2 closer to source 1
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='black', label_pos=0.5, font_size=10)

    plt.title("4-Node Directed Graph for Min-Cost Flow")
    plt.axis('off') # Hide the axes
    plt.show()

    # Optional: Print graph information to verify
    print("Nodes in the graph:", G.nodes)
    print("Edges in the graph (u, v, data):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v}: Capacity={data['capacity']}, Weight={data['weight']}")
        
    return G
# residual graph is not connected- the nx func canot work properly !!!
def build_and_draw_graph3():
    """
    Initializes the new node directed graph, adds edges with capacity and weight attributes,
    and visualizes the graph using fixed positions for layout.
    
    Returns:
        nx.DiGraph: The constructed graph G.
    """
    # 1. Initialize a directed graph
    G = nx.DiGraph()

    pos = {
        0: (0, 200),
        1: (150, 300),
        2: (150, 200),
        3: (150, 100),
        4: (300, 250),
        5: (300, 150),
        6: (450, 200),
    }

    # 2. Define Edges with Attributes
    # Format: (source, target, {'capacity': c, 'weight': w})
    # The attributes are derived from the 'e <source_id> <target_id> <edge_id> <capacity> <weight>' lines.
    edges_with_attributes = [
        # (u, v, capacity, weight)
        (0, 1, {'capacity': 8, 'weight': 2}),
        (0, 2, {'capacity': 6, 'weight': 1}),
        (1, 3, {'capacity': 3, 'weight': 5}),
        (2, 1, {'capacity': 2, 'weight': 1}),
        (2, 4, {'capacity': 5, 'weight': 2}),
        (3, 5, {'capacity': 4, 'weight': 1}),
        (3, 4, {'capacity': 1, 'weight': 3}),
        (4, 6, {'capacity': 7, 'weight': 1}),
        (5, 4, {'capacity': 2, 'weight': 1}),
        (5, 6, {'capacity': 5, 'weight': 3}),
        (2, 5, {'capacity': 4, 'weight': 1}),
    ]
    
    # 3. Add all edges and their attributes to the graph
    G.add_edges_from(edges_with_attributes)

    # 5. Extract edge labels for drawing
    # The label will be formatted as "(capacity, weight)"
    edge_labels = {
        (u, v): f"({d['capacity']},{d['weight']})"
        for u, v, d in G.edges(data=True)
    }

    # 6. Visualization settings
    plt.figure(figsize=(8, 5))

    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="#89CFF0", edgecolors="black", linewidths=1.5)

    # Draw the edges
    nx.draw_networkx_edges(G, pos, arrowsize=20, edge_color="black", width=2)

    # Draw node labels (the node numbers)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

    # Draw edge labels (the capacity and weight)
    # label_pos=0.3 is used for edge 1->2 to avoid overlap with node 6
    edge_label_pos = {p: 0.5 for p in pos}
    edge_label_pos[(1, 2)] = 0.3 # Move label for 1->2 closer to source 1
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='black', label_pos=0.5, font_size=10)

    plt.title("4-Node Directed Graph for Min-Cost Flow")
    plt.axis('off') # Hide the axes
    plt.show()

    # Optional: Print graph information to verify
    print("Nodes in the graph:", G.nodes)
    print("Edges in the graph (u, v, data):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v}: Capacity={data['capacity']}, Weight={data['weight']}")
        
    return G
#same as 3
def build_and_draw_graph4():
    """
    Initializes the graph based on the user's input, with one modification 
    to introduce a negative cycle (2 -> 1 -> 2) with cost -4.
    
    Returns:
        nx.DiGraph: The constructed graph G.
    """
    G = nx.DiGraph()

    # Node positions based on user input (n <x> <y> <node_id>)
    pos = {
        0: (0, 200),
        1: (150, 300),
        2: (150, 200),
        3: (150, 100),
        4: (300, 250),
        5: (300, 150),
        6: (450, 200),
    }

    # Edges based on user input (e <source> <target> <edge_id> <capacity> <weight>)
    edges_with_attributes = [
        # Original edges from user request
        (0, 1, {'capacity': 8, 'weight': 2}),
        (0, 2, {'capacity': 6, 'weight': 1}),
        # (1, 3, {'capacity': 3, 'weight': 5}), # Use this original edge
        (2, 1, {'capacity': 2, 'weight': 1}),
        (2, 4, {'capacity': 5, 'weight': 2}),
        (3, 5, {'capacity': 4, 'weight': 1}),
        (3, 4, {'capacity': 1, 'weight': 3}),
        (4, 6, {'capacity': 7, 'weight': 1}),
        (5, 4, {'capacity': 2, 'weight': 1}),
        (5, 6, {'capacity': 5, 'weight': 3}),
        (2, 5, {'capacity': 4, 'weight': 1}),
        (4, 1, {'capacity': 1, 'weight': 1}),
    ]
    
    G.add_edges_from(edges_with_attributes)

    # 5. Extract edge labels for drawing
    edge_labels = {
        (u, v): f"({d['capacity']},{d['weight']})"
        for u, v, d in G.edges(data=True)
    }

    # 6. Visualization settings
    plt.figure(figsize=(8, 6))

    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="#FFD700", edgecolors="black", linewidths=1.5)
    nx.draw_networkx_edges(G, pos, arrowsize=20, edge_color="black", width=2)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")
    
    nx.draw_networkx_edge_labels(
        G, pos, 
        edge_labels=edge_labels, 
        font_color='black', 
        label_pos=0.5, 
        font_size=10
    )

    plt.title("Directed Graph 4 (Min-Cost Test with Negative Cycle: 2→1→2)")
    plt.axis('off')
    plt.show()
        
    return G


def main():
    """
    Main entry point for the script.
    """
    
    G1 = build_and_draw_graph1()
    # Define source (s) and sink (t) for the Min-Cost Max-Flow problem
    source_node = 0
    sink_node = 5
    
    # Run the Cycle-Cancelling algorithm
    print(f"\n--- Running Cycle-Cancelling Algorithm from Node {source_node} to Node {sink_node} ---")
    
    try:
        flow_dict, min_cost = cycle_cancelling(
            G1, 
            source_node, 
            sink_node, 
            weight="weight", 
            capacity="capacity"
        )
        
        print("\n--- Results ---")
        print(f"Calculated Minimum Cost: {min_cost}")
        print("Final Flow Dictionary (u -> v: flow_amount):")
        
        total_flow = 0
        for u, nbrs in flow_dict.items():
            for v, f in nbrs.items():
                if f > 0:
                    print(f"  {u} -> {v}: {f}")
                    if u == source_node:
                        total_flow += f
        
        print(f"\nTotal Max Flow (Flow out of source {source_node}): {total_flow}")
    
    except Exception as e:
        print(f"\n--- Execution Error ---")
        print(f"The Cycle-Cancelling algorithm failed, likely due to a dependency on a non-standard NetworkX function (nx.find_negative_cycle) or an issue in flow augmentation logic.")
        print(f"Error details: {e}")

    """
    G2 = build_and_draw_graph2()

    # Define source (s) and sink (t) for the Min-Cost Max-Flow problem
    source_node = 0
    sink_node = 3
    
    # Run the Cycle-Cancelling algorithm
    print(f"\n--- Running Cycle-Cancelling Algorithm from Node {source_node} to Node {sink_node} ---")
    
    try:
        flow_dict, min_cost = cycle_cancelling(
            G2, 
            source_node, 
            sink_node, 
            weight="weight", 
            capacity="capacity"
        )
        
        print("\n--- Results ---")
        print(f"Calculated Minimum Cost: {min_cost}")
        print("Final Flow Dictionary (u -> v: flow_amount):")
        
        total_flow = 0
        for u, nbrs in flow_dict.items():
            for v, f in nbrs.items():
                if f > 0:
                    print(f"  {u} -> {v}: {f}")
                    if u == source_node:
                        total_flow += f
        
        print(f"\nTotal Max Flow (Flow out of source {source_node}): {total_flow}")
    
    except Exception as e:
        print(f"\n--- Execution Error ---")
        print(f"The Cycle-Cancelling algorithm failed, likely due to a dependency on a non-standard NetworkX function (nx.find_negative_cycle) or an issue in flow augmentation logic.")
        print(f"Error details: {e}")


    G3 = build_and_draw_graph3()
    # Define source (s) and sink (t) for the Min-Cost Max-Flow problem
    source_node = 0
    sink_node = 6
    
    # Run the Cycle-Cancelling algorithm
    print(f"\n--- Running Cycle-Cancelling Algorithm from Node {source_node} to Node {sink_node} ---")
    
    try:
        flow_dict, min_cost = cycle_cancelling(
            G3, 
            source_node, 
            sink_node, 
            weight="weight", 
            capacity="capacity"
        )
        
        print("\n--- Results ---")
        print(f"Calculated Minimum Cost: {min_cost}")
        print("Final Flow Dictionary (u -> v: flow_amount):")
        
        total_flow = 0
        for u, nbrs in flow_dict.items():
            for v, f in nbrs.items():
                if f > 0:
                    print(f"  {u} -> {v}: {f}")
                    if u == source_node:
                        total_flow += f
        
        print(f"\nTotal Max Flow (Flow out of source {source_node}): {total_flow}")
    
    except Exception as e:
        print(f"\n--- Execution Error ---")
        print(f"The Cycle-Cancelling algorithm failed, likely due to a dependency on a non-standard NetworkX function (nx.find_negative_cycle) or an issue in flow augmentation logic.")
        print(f"Error details: {e}")
    
    G4 = build_and_draw_graph4()

    # Define source (s) and sink (t) for the Min-Cost Max-Flow problem
    source_node = 2
    sink_node = 6
    
    # Run the Cycle-Cancelling algorithm
    print(f"\n--- Running Cycle-Cancelling Algorithm from Node {source_node} to Node {sink_node} ---")
    
    try:
        flow_dict, min_cost = cycle_cancelling(
            G4, 
            source_node, 
            sink_node, 
            weight="weight", 
            capacity="capacity"
        )
        
        print("\n--- Results ---")
        print(f"Calculated Minimum Cost: {min_cost}")
        print("Final Flow Dictionary (u -> v: flow_amount):")
        
        total_flow = 0
        for u, nbrs in flow_dict.items():
            for v, f in nbrs.items():
                if f > 0:
                    print(f"  {u} -> {v}: {f}")
                    if u == source_node:
                        total_flow += f
        
        print(f"\nTotal Max Flow (Flow out of source {source_node}): {total_flow}")
    
    except Exception as e:
        print(f"\n--- Execution Error ---")
        print(f"The Cycle-Cancelling algorithm failed, likely due to a dependency on a non-standard NetworkX function (nx.find_negative_cycle) or an issue in flow augmentation logic.")
        print(f"Error details: {e}")
        """



if __name__ == "__main__":
    main()
