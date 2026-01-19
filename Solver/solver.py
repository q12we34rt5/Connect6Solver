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
        
    def solve(self, simulations: int = 100):
        # 1. tree select (MCTS)
        # 2. call NCTU6 
        # 3. expand tree
        # 4. backpropagate 
        # 5. solve or not?

        if not self.tree.root:
            raise ValueError("No job set. Call set_job() first.")

        check_node = self.tree.root
        for i in range(simulations):
            print(f"Simulation {i+1}/{simulations}")
            # 1. Selection (done)
            leaf = self.tree.selection() 
            # print(node_to_move_string(leaf), i)
            # 2. Evaluation

            ignore_nodes = self.tree.collect_child_moves(leaf)
            ignore_parts = [node_to_move_string(n) for n in ignore_nodes]
            ignore_str = ";" + ";".join(ignore_parts)
            if leaf.num_children > 0:
                result = self.engine.evaluate(leaf, ignore=ignore_str)
            else:
                result = self.engine.evaluate(leaf)
            # print(result.state, node_to_move_string(result.moves))
            par = (leaf.parent).parent
            if par and i > 0:
                ignore_nodes2 = self.tree.collect_child_moves(par)
                ignore_parts2 = [node_to_move_string(n) for n in ignore_nodes2]
                ignore_str2 = ";" + ";".join(ignore_parts2)
                result2 = self.engine.evaluate(par, ignore=ignore_str2)
                self.tree.expand(par, result2, i)
                par = par.get_child(par.num_children - 1)
                par.status = result2.state
                self.tree.backpropagate(par, result2.score)

            # 3. Expansion
            self.tree.expand(leaf, result, i)
            leaf = leaf.get_child(leaf.num_children - 1)
            leaf.status = result.state
            # 4. Backpropagation
            self.tree.backpropagate(leaf, result.score)
            
            # Check if root is solved
            if self.tree.root.status != BoardState.UNKNOWN:
                break
