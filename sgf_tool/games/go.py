from ..node import BaseSGFNode


class Go:
    @staticmethod
    def compare_node(node1: BaseSGFNode, node2: BaseSGFNode) -> int:
        if 'B' in node1:
            if 'B' in node2:
                v1, v2 = node1['B'][0], node2['B'][0]
                return 0 if v1 == v2 else -1 if v1 < v2 else 1
            return -1
        if 'W' in node1:
            if 'W' in node2:
                v1, v2 = node1['W'][0], node2['W'][0]
                return 0 if v1 == v2 else -1 if v1 < v2 else 1
            return 1
        return 0
