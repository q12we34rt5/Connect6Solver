from .node import BaseSGFNode
import typing
from collections import deque
import functools
import bisect
import sys
import time


class DummyTimer:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def update(self, *args, **kwargs):
        pass


class Timer:
    def __init__(self, message="Processing", end="\n", file=sys.stderr):
        self.message = message
        self.end = end
        self.file = file

    def __enter__(self):
        self.start_time = time.time()
        print(f"{self.message}", end="", flush=True, file=self.file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        print(f" {elapsed_time:.2f}s", end=self.end, file=self.file)


class TrackingTimer:
    def __init__(self, message="Processing", total=0, end="\n", min_interval=0.1, file=sys.stderr):
        self.message = message
        self.total = total
        self.end = end
        self.current = 0
        self.min_interval = min_interval
        self.file = file

    def __enter__(self):
        self.start_time = time.time()
        if self.total == 0:
            print(f"{self.message} 0 0.00s", end="",
                  flush=True, file=self.file)
        else:
            print(f"{self.message} 0/{self.total} (0%) 0.00s",
                  end="", flush=True, file=self.file)
        self.last_time = self.start_time
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        if self.total == 0:
            print(f"\r{self.message} {self.current} {elapsed_time:.2f}s",
                  end=self.end, file=self.file)
        else:
            print(f"\r{self.message} {self.total}/{self.total} (100.00%) {elapsed_time:.2f}s",
                  end=self.end, file=self.file)

    def update(self, current):
        self.current = current
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        if current_time - self.last_time < self.min_interval:
            return
        if self.total == 0:
            print(f"\r{self.message} {current} {elapsed_time:.2f}s",
                  end="", flush=True, file=self.file)
        else:
            percentage = current / self.total * 100
            print(f"\r{self.message} {current}/{self.total} ({percentage:.2f}%) {elapsed_time:.2f}s",
                  end="", flush=True, file=self.file)
        self.last_time = current_time


class Algorithm:
    @staticmethod
    def dfs(root: BaseSGFNode, visit_func: typing.Callable[[BaseSGFNode, int], None]):
        """
        Depth-first search on the tree.
        """
        Algorithm._dfs(root, visit_func, 0)

    @staticmethod
    def _dfs(root: BaseSGFNode, visit_func: typing.Callable[[BaseSGFNode, int], None], depth: int):
        visit_func(root, depth)
        for child in root.get_children_iter():
            Algorithm._dfs(child, visit_func, depth + 1)

    @staticmethod
    def bfs(root: BaseSGFNode, visit_func: typing.Callable[[BaseSGFNode, int], None]):
        """
        Breadth-first search on the tree.
        """
        queue = deque([(root, 0)])
        while len(queue) > 0:
            current, depth = queue.popleft()
            visit_func(current, depth)
            for child in current.get_children_iter():
                queue.append((child, depth + 1))

    @staticmethod
    def dfs_iterator(root: BaseSGFNode):
        """
        Depth-first search iterator on the tree.
        """
        stack = [(root, 0)]
        while len(stack) > 0:
            current, depth = stack.pop()
            yield current, depth
            for child in reversed(list(current.get_children_iter())):
                stack.append((child, depth + 1))

    @staticmethod
    def bfs_iterator(root: BaseSGFNode):
        """
        Breadth-first search iterator on the tree.
        """
        queue = deque([(root, 0)])
        while len(queue) > 0:
            current, depth = queue.popleft()
            yield current, depth
            for child in current.get_children_iter():
                queue.append((child, depth + 1))

    @staticmethod
    def bottom_up_dfs(root: BaseSGFNode, visit_func: typing.Callable[[BaseSGFNode, int], None]):
        """
        Bottom-up depth-first search on the tree.
        """
        Algorithm._bottom_up_dfs(root, visit_func, 0)

    @staticmethod
    def _bottom_up_dfs(root: BaseSGFNode, visit_func: typing.Callable[[BaseSGFNode, int], None], depth: int):
        for child in list(root.get_children_iter()):
            Algorithm._bottom_up_dfs(child, visit_func, depth + 1)
        visit_func(root, depth)

    @staticmethod
    def bottom_up_bfs(root: BaseSGFNode, visit_func: typing.Callable[[BaseSGFNode, int], None]):
        """
        Bottom-up breadth-first search on the tree.
        """
        visited_nodes = []
        queue = deque([(root, 0)])
        while len(queue) > 0:
            current, depth = queue.popleft()
            visited_nodes.append((current, depth))
            for child in reversed(list(current.get_children_iter())):
                queue.append((child, depth + 1))
        for node, depth in reversed(visited_nodes):
            visit_func(node, depth)

    @staticmethod
    def bottom_up_dfs_iterator(root: BaseSGFNode):
        """
        Bottom-up depth-first search iterator on the tree.
        """
        yield from Algorithm._bottom_up_dfs_iterator(root, 0)

    @staticmethod
    def _bottom_up_dfs_iterator(root: BaseSGFNode, depth: int):
        for child in list(root.get_children_iter()):
            yield from Algorithm._bottom_up_dfs_iterator(child, depth + 1)
        yield root, depth

    @staticmethod
    def bottom_up_bfs_iterator(root: BaseSGFNode):
        """
        Bottom-up breadth-first search iterator on the tree.
        """
        visited_nodes = []
        queue = deque([(root, 0)])
        while len(queue) > 0:
            current, depth = queue.popleft()
            visited_nodes.append((current, depth))
            for child in reversed(list(current.get_children_iter())):
                queue.append((child, depth + 1))
        for node, depth in reversed(visited_nodes):
            yield node, depth

    @staticmethod
    def find_nodes_with_property(root: BaseSGFNode, tag: str, value: str, value_index: int = 0) -> typing.List[BaseSGFNode]:
        """
        Find nodes with a specific property.
        """
        results = []

        def visit_func(n, _):
            if tag in n:
                values = n[tag]
                if len(values) > value_index and values[value_index] == value:
                    results.append(n)

        Algorithm.dfs(root, visit_func)
        return results

    @staticmethod
    def binary_search(sorted_list, item, comparator):
        """
        Perform a binary search to find the index of an item in a sorted list using a comparator.
        Returns the index of the item if found, otherwise returns -1.
        """
        lo, hi = 0, len(sorted_list)
        while lo < hi:
            mid = (lo + hi) // 2
            cmp_result = comparator(sorted_list[mid], item)
            if cmp_result == 0:
                return mid
            elif cmp_result < 0:
                lo = mid + 1
            else:
                hi = mid
        return -1

    @staticmethod
    def bisect_left_with_comparator(sorted_list, item, comparator):
        """
        Perform a binary search to find the index of an item in a sorted list using a comparator.
        Returns the index of the item if found, otherwise returns -1.
        """
        class ComparatorWrapper:
            def __init__(self, item):
                self.item = item

            def __gt__(self, other):
                return comparator(self.item, other) > 0

        index = bisect.bisect_left(sorted_list, ComparatorWrapper(item))
        if index < len(sorted_list) and comparator(sorted_list[index], item) == 0:
            return index
        return -1

    @staticmethod
    def merge_tree(root: BaseSGFNode, other_root: BaseSGFNode, comparator: typing.Callable[[BaseSGFNode, BaseSGFNode],
                   int], merge_func: typing.Optional[typing.Callable[[BaseSGFNode, BaseSGFNode], None]] = None):
        """
        Merge two trees.

        The two trees must have the same root node. After merging, the nodes in the second tree (other_root) will be merged into the first tree (root).
        Common nodes will remain unchanged, and differing nodes in the second tree will be moved to the first tree.

        Args:
            root (BaseSGFNode): The root node of the first tree.
            other_root (BaseSGFNode): The root node of the second tree.
            comparator (Callable[[BaseSGFNode, BaseSGFNode], int]): A function to compare two nodes.
                - Returns 0 if the nodes are equal.
                - Returns -1 if the first node is less than the second node.
                - Returns 1 if the first node is greater than the second node.
            merge_func (Callable[[BaseSGFNode, BaseSGFNode], None], optional): A function called when two nodes are equal.
                If provided, it can be used to merge the properties of the two nodes by modifying the properties of the first node.

        Raises:
            ValueError: If the root nodes of the two trees are not equal according to the comparator.
        """
        if comparator(root, other_root) != 0:
            raise ValueError("The two roots are not equal.")
        Algorithm._merge_tree(root, other_root, comparator, merge_func)

    @staticmethod
    def _merge_tree(root: BaseSGFNode, other_root: BaseSGFNode, comparator: typing.Callable[[BaseSGFNode, BaseSGFNode],
                    int], merge_func: typing.Optional[typing.Callable[[BaseSGFNode, BaseSGFNode], None]] = None):
        # store the children in a list to avoid modifying the tree while merging
        sorted_nodes = sorted(root.get_children_iter(),
                              key=functools.cmp_to_key(comparator))
        other_nodes = list(other_root.get_children_iter())

        if merge_func is not None:
            merge_func(root, other_root)

        # TODO: raise error if children have duplicates
        for child in other_nodes:
            index = Algorithm.binary_search(sorted_nodes, child, comparator)
            if index != -1:
                Algorithm.merge_tree(
                    sorted_nodes[index], child, comparator, merge_func)
            elif index == -1:
                root.add_child(child.detach())
