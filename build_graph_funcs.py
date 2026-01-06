import networkx as nx
from copy import deepcopy
import matplotlib.pyplot as plt

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

    """
    # Optional: Print graph information to verify
    print("Nodes in the graph:", G.nodes)
    print("Edges in the graph (u, v, data):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v}: Capacity={data['capacity']}, Weight={data['weight']}")
    """
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

    """
    # Optional: Print graph information to verify
    print("Nodes in the graph:", G.nodes)
    print("Edges in the graph (u, v, data):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v}: Capacity={data['capacity']}, Weight={data['weight']}")
    """
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

    """
    # Optional: Print graph information to verify
    print("Nodes in the graph:", G.nodes)
    print("Edges in the graph (u, v, data):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v}: Capacity={data['capacity']}, Weight={data['weight']}")
    """
        
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

def build_and_draw_graph20():
    """
    Builds your custom 20-node directed graph with given positions and edges.
    Draws the graph with (capacity, weight) labels.
    """
    # 1. Initialize directed graph
    G = nx.DiGraph()

    # 2. Define the edges with attributes: (src, dst, {'capacity': c, 'weight': w})
    edges_with_attributes = [
        (0, 1, {'capacity': 8, 'weight': 2}),
        (0, 2, {'capacity': 6, 'weight': 1}),
        (2, 1, {'capacity': 2, 'weight': 1}),
        (2, 5, {'capacity': 5, 'weight': 2}),
        (3, 6, {'capacity': 4, 'weight': 1}),
        (3, 7, {'capacity': 1, 'weight': 3}),
        (4, 7, {'capacity': 2, 'weight': 1}),
        (4, 8, {'capacity': 7, 'weight': 3}),
        (5, 9, {'capacity': 5, 'weight': 1}),
        (5, 6, {'capacity': 3, 'weight': 2}),
        (6, 10, {'capacity': 4, 'weight': 1}),
        (7, 11, {'capacity': 6, 'weight': 2}),
        (8, 12, {'capacity': 3, 'weight': 3}),
        (9, 13, {'capacity': 7, 'weight': 1}),
        (10, 14, {'capacity': 2, 'weight': 1}),
        (11, 15, {'capacity': 4, 'weight': 3}),
        (12, 16, {'capacity': 5, 'weight': 2}),
        (13, 17, {'capacity': 3, 'weight': 2}),
        (14, 18, {'capacity': 4, 'weight': 1}),
        (15, 19, {'capacity': 6, 'weight': 3}),
        (6, 3, {'capacity': 2, 'weight': 1}),
        (10, 5, {'capacity': 1, 'weight': 2}),
        (14, 10, {'capacity': 3, 'weight': 1}),
        (18, 15, {'capacity': 2, 'weight': 2}),
        (17, 14, {'capacity': 5, 'weight': 1}),
    ]

    G.add_edges_from(edges_with_attributes)

    # 3. Node positions matching your "n x y id" values (converted to a cleaner scale)
    pos = {
        0: (0, 300),
        1: (150, 350),
        2: (150, 250),
        3: (150, 150),
        4: (150, 50),
        5: (300, 300),
        6: (300, 200),
        7: (300, 100),
        8: (300, 0),
        9: (450, 350),
        10: (450, 250),
        11: (450, 150),
        12: (450, 50),
        13: (600, 300),
        14: (600, 200),
        15: (600, 100),
        16: (600, 0),
        17: (750, 250),
        18: (750, 150),
        19: (750, 50)
    }

    # 4. Create edge labels in the format "(capacity,weight)"
    edge_labels = {(u, v): f"({d['capacity']},{d['weight']})"
                   for u, v, d in G.edges(data=True)}

    # 5. Draw the graph
    plt.figure(figsize=(16, 8))
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color="#C2E8FF",
                           edgecolors="black", linewidths=1.5)
    nx.draw_networkx_edges(G, pos, arrowsize=20, width=2)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                 font_size=8, label_pos=0.5)

    plt.title("20-Node Directed Graph (Capacity, Weight)")
    plt.axis("off")
    plt.show()

    """
    # Optional: Print graph information to verify
    print("Nodes in the graph:", G.nodes)
    print("Edges in the graph (u, v, data):")
    for u, v, data in G.edges(data=True):
        print(f"  {u} -> {v}: Capacity={data['capacity']}, Weight={data['weight']}")
    """

    return G