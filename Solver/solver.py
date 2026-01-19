import typing
from .engine import NCTU6Engine
from .tree import MCTS
from .types import BoardState, EvaluationResult
from .utils import node_to_move_string

class Solver:

    def __init__(self, executable_path: typing.Optional[str] = None):
        self.engine = NCTU6Engine(executable_path=executable_path)
        self.tree = MCTS()

    def set_job(self, job: str):
        self.tree.load_sgf(job)
        # set board state to solve

    def expand_node(self, node, id: int):
        # print(f'node {node}, parent {node.parent}, child {node.get_child(0)}')
        ignore_nodes = self.tree.collect_child_moves(node)
        ignore_parts = [node_to_move_string(n) for n in ignore_nodes]
        ignore_str = ";" + ";".join(ignore_parts)
        if node.num_children > 0:
            result = self.engine.evaluate(node, ignore=ignore_str)
        else:
            result = self.engine.evaluate(node)
        print(result.moves, result.score)
        # print("======check again======")
        # print(f'node {node}, parent {node.parent}, child {node.get_child(0)}')
        # if node.num_children > 0:
            # print(result.moves, result.moves.get_child(0))
            # print(node.get_child(node.num_children - 1), node.get_child(node.num_children - 1).get_child(0))
        if node.num_children > 0 and str(result.moves) == str(node.get_child(node.num_children - 1)) and str(result.moves.get_child(0)) == str(node.get_child(node.num_children - 1).get_child(0)):
            # print(f'parent {node.parent}, node{node}, child {node.get_child(0)}')
            node.parent.status = node.get_child(0).status
            return 0

        self.tree.expand(node, result, id)
        node = node.get_child(node.num_children - 1)
        node.status = result.state
        # 4. Backpropagation
        self.tree.backpropagate(node, result.score)
        return 1
        
        
    def solve(self, simulations: int = 100):
        # 1. tree select (MCTS)
        # 2. call NCTU6 
        # 3. expand tree
        # 4. backpropagate 
        # 5. solve or not?

        if not self.tree.root:
            raise ValueError("No job set. Call set_job() first.")
        # print(self.tree.root, self.tree.root.parent)
        check_node = self.tree.root
        i = 0
        while i < simulations:
            print(f"Simulation {i+1}/{simulations}")
            # 1. Selection (done)
            leaf = self.tree.selection() 
            print(leaf, leaf.parent)
            if leaf.parent.id == 0 and i > 0:
                break
            # print(node_to_move_string(leaf), i)
            # 2. Evaluation
            # can't find another way to go
            if self.expand_node(leaf, i + 1) == 0:
                continue
            par = (leaf.parent).parent
            if par and i > 0:
                self.expand_node(par, i + 1)
            i += 1
            if self.tree.root.status != BoardState.UNKNOWN:
                break
