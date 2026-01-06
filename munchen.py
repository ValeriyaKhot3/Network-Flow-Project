import math
import networkx as nx
from typing import Hashable, Tuple, Dict, Any


class CycleCancellingAlgorithm:
    """
    Cycle Cancelling minimum-cost flow algorithm with
    an Edmonds–Karp-style max-flow initialization.

    This is a Python translation of the algorithmic core of the
    JavaScript CycleCancellingAlgorithm you posted.

    Assumptions:
    - G is a networkx.DiGraph
    - Edge attributes:
        * capacity_attr: capacity (>= 0)
        * weight_attr:   cost per unit of flow (can be negative)
    - We store and update an additional edge attribute 'flow'.

    Usage:
        algo = CycleCancellingAlgorithm(G, s, t)
        flow_dict, min_cost = algo.run()
    """

    def __init__(
        self,
        G: nx.DiGraph,
        source: Hashable,
        target: Hashable,
        *,
        capacity_attr: str = "capacity",
        weight_attr: str = "weight",
    ) -> None:
        if not isinstance(G, nx.DiGraph):
            raise TypeError("G must be a networkx.DiGraph")

        if source not in G:
            raise ValueError("Source node does not exist in graph.")
        if target not in G:
            raise ValueError("Target node does not exist in graph.")

        self.G: nx.DiGraph = G
        self.s: Hashable = source
        self.t: Hashable = target
        self.capacity_attr: str = capacity_attr
        self.weight_attr: str = weight_attr

        # Initialize flow on edges
        for u, v in self.G.edges():
            self.G[u][v]["flow"] = 0

        # State variables similar to JS 'state'
        self.cycle = []           # list of dicts {edge:(u,v), direction:+1/-1}
        self.cycle_min_flow = 0.0
        self.no_cycle_found = False

    # ---------------------------------------------------------
    # Public entry point
    # ---------------------------------------------------------
    def run(self) -> Tuple[Dict[Hashable, Dict[Hashable, float]], float]:
        """
        Run the full algorithm:
        1. Initialize to max flow using BFS residual search (Edmonds–Karp style).
        2. Repeatedly find negative cycles in residual graph and adjust.

        Returns:
            (flow_dict, min_cost)
        """
        self._get_max_flow()
        self._main_loop()

        flow_dict = self._build_flow_dict()
        min_cost = self._compute_total_cost()

        return flow_dict, min_cost

    # ---------------------------------------------------------
    # Step 1: Max-flow initialization (Edmonds–Karp style)
    # ---------------------------------------------------------
    def _get_max_flow(self) -> None:
        """
        Initialize the flow to a maximum s-t flow using BFS
        in the residual graph, following the JS getMaxFlow().
        """

        # Ensure flow = 0 on all edges (like JS)
        for u, v in self.G.edges():
            self.G[u][v]["flow"] = 0

        while True:
            # predecessor[node] = {
            #     "node": previous_node,
            #     "edge": (u,v),
            #     "residual_capacity": ...,
            #     "direction": +1/-1
            # }
            predecessor: Dict[Hashable, Dict[str, Any]] = {n: None for n in self.G.nodes()}
            queue = [self.s]
            predecessor[self.s] = {"node": None, "edge": None, "residual_capacity": math.inf, "direction": 0}

            # BFS in residual graph
            while predecessor[self.t] is None and queue:
                node = queue.pop(0)

                # Forward residual edges: (node -> v) with capacity > flow
                for _, v, data in self.G.out_edges(node, data=True):
                    cap = data.get(self.capacity_attr, 0)
                    flow = data.get("flow", 0)
                    if cap > flow and predecessor[v] is None:
                        residual_cap = cap - flow
                        predecessor[v] = {
                            "node": node,
                            "edge": (node, v),
                            "residual_capacity": residual_cap,
                            "direction": +1,
                        }
                        queue.append(v)

                # Backward residual edges: (u -> node) with flow > 0
                for u, _, data in self.G.in_edges(node, data=True):
                    flow = data.get("flow", 0)
                    if flow > 0 and predecessor[u] is None:
                        residual_cap = flow
                        predecessor[u] = {
                            "node": node,
                            "edge": (u, node),
                            "residual_capacity": residual_cap,
                            "direction": -1,
                        }
                        queue.append(u)

            if predecessor[self.t] is None:
                # No augmenting path
                break

            # Reconstruct path and find bottleneck
            path = []
            augmentation = math.inf
            current = self.t
            while current != self.s:
                pred_info = predecessor[current]
                path.append(pred_info)
                augmentation = min(augmentation, pred_info["residual_capacity"])
                current = pred_info["node"]

            # Apply augmentation
            for step in path:
                u, v = step["edge"]
                direction = step["direction"]
                self.G[u][v]["flow"] = self.G[u][v].get("flow", 0) + direction * augmentation

        # Finished max flow, like JS: state.current_step = STEP_MAINLOOP

    # ---------------------------------------------------------
    # Step 2: Main loop: find negative cycles, adjust, repeat
    # ---------------------------------------------------------
    def _main_loop(self) -> None:
        """
        Repeatedly try to find a negative cycle in the residual graph
        and adjust flow along it.
        """
        while True:
            self.no_cycle_found = False
            self._find_negative_cycle()

            if self.no_cycle_found:
                # No negative cycle: we are at a min-cost flow
                break

            self._adjust_cycle()
            # Then try again

    # ---------------------------------------------------------
    # Bellman-Ford style search for negative cycle in residual
    # ---------------------------------------------------------
    def _find_negative_cycle(self) -> None:
        """
        Translates the JS findNegativeCycle() logic.

        We keep:
            node_distance[node]  ~ node.state.distance
            predecessor[node]    ~ node.state.predecessor:
                {
                    "prev_node": ...,
                    "edge": (u,v),
                    "direction": +1/-1
                }
        """
        # Initialize distances and predecessors
        node_distance = {n: math.inf for n in self.G.nodes()}
        predecessor: Dict[Hashable, Dict[str, Any]] = {n: None for n in self.G.nodes()}

        # JS sets target distance = 0
        node_distance[self.t] = 0.0

        # Relax edges |V| times
        nodes_list = list(self.G.nodes())
        num_nodes = len(nodes_list)

        for _ in range(num_nodes):
            updated = False
            for u, v, data in self.G.edges(data=True):
                cap = data.get(self.capacity_attr, 0)
                flow = data.get("flow", 0)
                weight = data.get(self.weight_attr, 0)

                # Forward residual edge if cap > flow, cost = +weight
                if cap > flow and node_distance[u] + weight < node_distance[v]:
                    node_distance[v] = node_distance[u] + weight
                    predecessor[v] = {
                        "prev_node": u,
                        "edge": (u, v),
                        "direction": +1,
                    }
                    updated = True

                # Backward residual edge if flow > 0, cost = -weight
                if flow > 0 and node_distance[v] - weight < node_distance[u]:
                    node_distance[u] = node_distance[v] - weight
                    predecessor[u] = {
                        "prev_node": v,
                        "edge": (u, v),
                        "direction": -1,
                    }
                    updated = True

            if not updated:
                break  # early stop if no update in this iteration

        # Check for negative cycle: if any edge can still be relaxed
        has_cycle = False
        for u, v, data in self.G.edges(data=True):
            cap = data.get(self.capacity_attr, 0)
            flow = data.get("flow", 0)
            weight = data.get(self.weight_attr, 0)

            if cap > flow and node_distance[u] + weight < node_distance[v]:
                has_cycle = True
                break

            if flow > 0 and node_distance[v] - weight < node_distance[u]:
                has_cycle = True
                break

        self.no_cycle_found = not has_cycle

        if not has_cycle:
            # Nothing else to do
            self.cycle = []
            self.cycle_min_flow = 0.0
            return

        # JS logic to reconstruct a cycle (somewhat ad-hoc, starting from target)
        # We mimic it as closely as possible.
        self.cycle = []
        self.cycle_min_flow = math.inf

        cycle_node_stack = [self.t]
        searching = True

        while searching:
            last_node = cycle_node_stack[-1]
            pred_info = predecessor[last_node]
            if pred_info is None:
                # In case the JS code's assumption doesn't hold,
                # we break to avoid KeyError.
                break

            new_node = pred_info["prev_node"]
            self.cycle.append(pred_info)

            # check if new_node already in stack
            if new_node in cycle_node_stack:
                # remove prefix up to first occurrence of new_node
                idx = cycle_node_stack.index(new_node)
                cycle_node_stack = cycle_node_stack[idx:]
                self.cycle = self.cycle[idx:]
                searching = False
            else:
                cycle_node_stack.append(new_node)

        # Determine bottleneck (cycle_min_flow)
        for step in self.cycle:
            u, v = step["edge"]
            direction = step["direction"]
            data = self.G[u][v]
            cap = data.get(self.capacity_attr, 0)
            flow = data.get("flow", 0)

            if direction == +1:
                residual_cap = cap - flow
            else:
                residual_cap = flow

            self.cycle_min_flow = min(self.cycle_min_flow, residual_cap)

    # ---------------------------------------------------------
    # Adjust flow along found cycle
    # ---------------------------------------------------------
    def _adjust_cycle(self) -> None:
        """
        Adjust flow using the found negative cycle, like JS adjustCycle().
        """
        if not self.cycle or self.cycle_min_flow <= 0:
            return

        for step in self.cycle:
            u, v = step["edge"]
            direction = step["direction"]
            self.G[u][v]["flow"] = self.G[u][v].get("flow", 0) + direction * self.cycle_min_flow

        # Reset cycle state
        self.cycle = []
        self.cycle_min_flow = 0.0

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _compute_total_cost(self) -> float:
        """
        Total cost = sum_e flow_e * weight_e
        """
        total_cost = 0.0
        for u, v, data in self.G.edges(data=True):
            flow = data.get("flow", 0)
            weight = data.get(self.weight_attr, 0)
            total_cost += flow * weight
        return total_cost

    def _build_flow_dict(self) -> Dict[Hashable, Dict[Hashable, float]]:
        """
        Build a flow_dict in the style of networkx.maximum_flow.
        """
        flow_dict: Dict[Hashable, Dict[Hashable, float]] = {u: {} for u in self.G.nodes()}
        for u, v, data in self.G.edges(data=True):
            flow_dict[u][v] = data.get("flow", 0)
        return flow_dict
    
def cycle_cancelling(
    G: nx.DiGraph,
    s: Hashable,
    t: Hashable,
    *,
    weight: str = "weight",
    flow_func=None,                 # kept for compatibility, not used
    capacity: str = "capacity",
    negative_cycle_func=None        # kept for compatibility, not used
) -> Tuple[Dict[Hashable, Dict[Hashable, float]], float]:
    """
    Compatibility wrapper so you can call this exactly like your
    previous `cycle_cancelling` from MultiR.
    """
    algo = CycleCancellingAlgorithm(
        G,
        source=s,
        target=t,
        capacity_attr=capacity,
        weight_attr=weight,
    )
    return algo.run()
