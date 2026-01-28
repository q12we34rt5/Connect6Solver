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

    def expand(self, node: SolverNode, result: EvaluationResult, id: int):
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
                move.id = id
                node.add_child(move)

    def backpropagate(self, node: SolverNode, score):
        # the node is the first move
        current = node
        
        while True:
            current.visit_count += 1
            current.winrate += score
            if current.child:
                # let the state can be transfered to root
                if current == self.root:
                    children = current.child
                    current.status = children.status
                elif current.id == 0 and current.child.child.id == 0:
                    children = current.child.child
                    current.status = children.status
                elif "W" in current:
                    children = current.child.child
                    while children:
                        if children.status == BoardState.BLACK_WIN:
                            current.status = BoardState.BLACK_WIN
                            break
                        children = children.next_sibling
                elif "B" in current:
                    children = current.child.child
                    if current == self.root:
                        children = current.child
                    while children:
                        if children.status == BoardState.WHITE_WIN:
                            current.status = BoardState.WHITE_WIN
                            break
                        children = children.next_sibling

            if current == self.root:
                break
            if self.root == current.parent:
                current = current.parent
                continue 

            current = (current.parent).parent

    def update_state(self, node: SolverNode):
        # the node is the first move
        current = node
        
        while True:
            if current == self.root:
                break
            elif current.parent == self.root:
                current = current.parent
            else:
                current = current.parent.parent

            # let the state can be transfered to root
            if current == self.root:
                children = current.child
                current.status = children.status
            elif current.id == 0 and current.child.child.id == 0:
                children = current.child.child
                current.status = children.status
            elif "W" in current:
                children = current.child.child
                while children:
                    if children.status == BoardState.BLACK_WIN:
                        current.status = BoardState.BLACK_WIN
                        break
                    children = children.next_sibling
            elif "B" in current:
                children = current.child.child
                if current == self.root:
                    children = current.child
                while children:
                    if children.status == BoardState.WHITE_WIN:
                        current.status = BoardState.WHITE_WIN
                        break
                    children = children.next_sibling


class MCTS(Tree):

    def __init__(self):
        super().__init__()
        self.c = math.sqrt(2)

    def selection(self):
        now_node = self.root
        while now_node.num_children > 0:
            parent_visit_count = now_node.visit_count 
            children = now_node.child 
            index = 0
            max_child_id = -1
            max_child_value = -1e18
            
            while children:
                # don't choose always win node
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
            
            # all the children are determined
            if max_child_id == -1:
                break
            now_node = now_node.get_child(max_child_id)
            now_node = now_node.get_child(0)
        
        return now_node
