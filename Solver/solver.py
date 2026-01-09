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

        for i in range(simulations):
            # 1. Selection (done)
            leaf = self.tree.selection() 
            
            # If leaf is terminal (already solved), we treat it as a result
            if leaf.status != BoardState.UNKNOWN:
                score = 1.0 if leaf.status == BoardState.BLACK_WIN else -1.0
                result = EvaluationResult(
                    moves=None,
                    score=score,
                    state=leaf.status,
                    info={"comment": "Terminal node revisit"},
                    raw=""
                )
                self.tree.backpropagate(leaf, result)
                continue

            # 2. Evaluation
            result = self.engine.evaluate(leaf)
            par = leaf.parent
            if par:
                # ignore_str = self.tree.collect_child_moves(par).to_sgf(root=NULL)
                ignore_nodes = self.tree.collect_child_moves(par)
                ignore_parts = [node_to_move_string(n) for n in ignore_nodes]
                ignore_str = ";" + ";".join(ignore_parts)
                result2 = self.engine.evaluate(par, ignore=ignore_str)
                self.tree.expand(par, result2)
                self.tree.backpropagate(par, result2)

            # 3. Expansion
            self.tree.expand(leaf, result)
            # 4. Backpropagation
            self.tree.backpropagate(leaf, result)
            
            # Check if root is solved
            if self.tree.root.status != BoardState.UNKNOWN:
                break
