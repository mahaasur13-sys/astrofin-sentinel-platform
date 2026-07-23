class SwarmDAG:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, node_id, data=None):
        self.nodes[node_id] = data

    def add_edge(self, a, b):
        self.edges.append((a, b))


class CausalMergeProtocol:
    def __init__(self):
        self.dag = SwarmDAG()

    def merge(self, a, b):
        self.dag.add_edge(a, b)
        return f"{a}->{b}"
