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
