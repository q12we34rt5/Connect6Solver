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
        if node.parent.id == 0:
            if node.child and node.child.id == 0:
                return 2
                
        ignore_nodes = self.tree.collect_child_moves(node)
        ignore_parts = [node_to_move_string(n) for n in ignore_nodes]
        ignore_str = ";" + ";".join(ignore_parts)
        if node.num_children > 0:
            result = self.engine.evaluate(node, ignore=ignore_str)
        else:
            result = self.engine.evaluate(node)
        
        #to check whether the move is the same as the last move
        if node.num_children > 0:
            same = False
            node_children = node.get_child(0)
            while node_children:
                if str(result.moves) == str(node_children) and str(result.moves.get_child(0)) == str(node_children.get_child(0)):
                    same = True
                    break
                node_children = node_children.next_sibling
            #check all children are black win or white win
            if same:
                w_win = 1
                b_win = 1
                node_children = node.get_child(0)
                while node_children:
                    if node_children.status == BoardState.WHITE_WIN:
                        b_win = 0
                    elif node_children.status == BoardState.BLACK_WIN:
                        w_win = 0
                    else:
                        b_win = 0
                        w_win = 0
                    node_children = node_children.next_sibling
                if w_win == 1:
                    node.parent.status = BoardState.WHITE_WIN
                elif b_win == 1:
                    node.parent.status = BoardState.BLACK_WIN
                else:
                    node.parent.status = BoardState.UNKNOWN

                self.tree.update_state(node.parent) 
                return 0

        self.tree.expand(node, result, id)
        node = node.get_child(node.num_children - 1)
        node.status = result.state
        

        self.tree.backpropagate(node, result.score)
        return 1
        
        
    def solve(self, simulations: int = 100):
        # 1. tree select (MCTS)
        # 2. call NCTU6 
        # 3. expand tree
        # 4. backpropagate 
        # 5. solve or not?

        check_node = self.tree.root
        simulation_step = 0
        while simulation_step < simulations:
            if self.tree.root.status != BoardState.UNKNOWN:
                break
            print(f"Simulation {simulation_step+1}/{simulations}")

            leaf = self.tree.selection() 
            
            expand_result = self.expand_node(leaf, simulation_step + 1)
            if expand_result == 0:
                gg = leaf.child
                while gg:
                    print(gg, gg.status, gg.child, gg.id)
                    gg = gg.next_sibling
                continue
            elif expand_result == 2:
                print("It shouldn't happen")
                break
            par = (leaf.parent).parent
            self.expand_node(par, simulation_step + 1)
            simulation_step += 1
