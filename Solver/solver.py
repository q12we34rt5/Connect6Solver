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

    def totally_win(node):
        if node.num_children == 0:
            return False
        now_child = node.get_child(0)
        while now_child:
            if now_child.status != BoardState.WHITE_WIN and now_child.status != BoardState.BLACK_WIN:
                return False
            now_child = now_child.next_sibling

        return True

    def branch_win(node):
        now_child = node.get_child(0)
        while now_child:
            if now_child.status == BoardState.WHITE_WIN or now_child.status == BoardState.BLACK_WIN:
                return True 
            now_child = now_child.next_sibling
        
        return False

    def expand_node(self, node, id: int):
        # print(id, node.parent.id, node.num_children)
        # if node.parent.id == 0:
        #     if node.child and node.child.id == 0:
        #         return 2
                
        ####################
        # if Solver.totally_win(node):
        #     if node.parent:
        #         node.parent.status = node.get_child(0).status
        #     else:
        #         node.status = node.get_child(0).status
        #     return

        ####################

        ignore_nodes = self.tree.collect_child_moves(node)
        ignore_str = ','.join([';' + ';'.join([node_to_move_string(nn) for nn in n]) for n in ignore_nodes])
        # ignore_str = ";" + ";".join(ignore_parts) if ignore_parts else ""
        # print(ignore_str)
        # print(f'num_child{node.num_children}')
        if node.num_children > 0:
            result = self.engine.evaluate(node, ignore=ignore_str)
        else:
            result = self.engine.evaluate(node)

        # print(result.state, result.score)
        # print(node_to_move_string(node.parent))
        
        # print(f'parent{node.parent.id}')
        # print(result.moves, result.moves.get_child(0))

        

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
                continue
            # elif expand_result == 2:
            #     print("It shouldn't happen")
            #     break
            print("expand another")
            par = (leaf.parent).parent
            self.expand_node(par, simulation_step + 1)
            simulation_step += 1
