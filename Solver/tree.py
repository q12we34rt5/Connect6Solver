import typing
import math
import random
import sgf_tool
from .solver_node import SolverNode, SolverNodeAllocator
from .types import BoardState, EvaluationResult

from .utils import node_to_move_string

class Tree:

    def __init__(self, node_allocator: typing.Optional[sgf_tool.parser.NodeAllocator[SolverNode]] = None):
        self.node_allocator = node_allocator or SolverNodeAllocator()
        self.root: typing.Optional[SolverNode] = None

    def load_sgf(self, sgf: str):
        self.root = sgf_tool.SGFParser(
            node_allocator=self.node_allocator).parse(sgf)

    def collect_child_moves(self, node: SolverNode):
        child = node.child
        all_moves = []  
        while child:
            all_moves.append(child)
            all_moves.append(child.get_child(0))
            child = child.next_sibling
        return all_moves

    def expand(self, node: SolverNode, result: EvaluationResult):
        if result.state == BoardState.BLACK_WIN:
            node.status = BoardState.BLACK_WIN
        elif result.state == BoardState.WHITE_WIN:
            node.status = BoardState.WHITE_WIN

        if result.moves:
            # print(f'checkmove{node_to_move_string(result.moves)}')
            # print(f'checkmove{node_to_move_string(result.moves.get_child(0))}')
            # Collect all siblings from the result.moves
            moves = []
            ptr = result.moves
            while ptr:
                moves.append(ptr)
                ptr = ptr.next_sibling

            for move in moves:
                node.add_child(move)

    def backpropagate(self, node: SolverNode, score):
        current = node
        # print("hello\n")
        while True:
            # print(current.status, node_to_move_string(current))
            current.visit_count += 1
            current.winrate += score
            if current.child:
                if "W" in current:
                    children = current.child.child
                    win_count = 0
                    while children:
                        # print(f'children {node_to_move_string(children)}')
                        if children.status == BoardState.BLACK_WIN:
                            current.status = BoardState.BLACK_WIN
                            break
                        elif children.status == BoardState.WHITE_WIN:
                            win_count += 1
                        else:
                            win_count = -1e18
                        children = children.next_sibling
                    if win_count >= 3:
                        current.status = BoardState.WHITE_WIN
                if "B" in current:
                    children = current.child.child
                    if current == self.root:
                        children = current.child
                    win_count = 0
                    while children:
                        # print(f'children {node_to_move_string(children)}')
                        if children.status == BoardState.WHITE_WIN:
                            current.status = BoardState.WHITE_WIN
                            break
                        elif children.status == BoardState.BLACK_WIN:
                            win_count += 1
                        else:
                            win_count = -1e18
                        children = children.next_sibling
                    if win_count >= 3:
                        current.status = BoardState.BLACK_WIN
                    if win_count >= 1 and current == self.root:
                        current.status = BoardState.BLACK_WIN

            if self.root == current.parent:
                current = current.parent
                continue 
            elif current == self.root:
                break

            current = (current.parent).parent


class MCTS(Tree):

    def __init__(self):
        super().__init__()
        self.c = math.sqrt(2)

    def selection(self):
        # don't choose always win node
        now_node = self.root
        first_choose = True
        while now_node.num_children > 0:
            parent_visit_count = now_node.visit_count 
            children = now_node.child 
            index = 0
            max_child_id = -1
            max_child_value = -1e18
            
            while children:
                if children.status != BoardState.UNKNOWN:
                    children = children.next_sibling
                    index += 1
                    continue
                nowscore = 0
                if children.visit_count == 0 or parent_visit_count == 0:
                    nowscore = 1e18
                else:
                    if "B" in children:
                        nowscore = children.winrate / (children.visit_count) + self.c * math.sqrt(math.log(parent_visit_count) / (children.visit_count))
                    elif "W" in children:
                        nowscore = -children.winrate / (children.visit_count) + self.c * math.sqrt(math.log(parent_visit_count) / (children.visit_count))
                
                if nowscore > max_child_value:
                    max_child_value = nowscore
                    max_child_id = index

                children = children.next_sibling
                index += 1
            
            if max_child_id == -1:
                break
            now_node = now_node.get_child(max_child_id)
            now_node = now_node.get_child(0)
        
        return now_node
