import typing
import math
import random
import sgf_tool
from .solver_node import SolverNode, SolverNodeAllocator
from .types import BoardState, EvaluationResult


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
            child = child.next_sibling
        return all_moves

    def expand(self, node: SolverNode, result: EvaluationResult):
        if result.state == BoardState.BLACK_WIN:
            node.status = BoardState.BLACK_WIN
        elif result.state == BoardState.WHITE_WIN:
            node.status = BoardState.WHITE_WIN

        if result.moves:
            # Collect all siblings from the result.moves
            moves = []
            ptr = result.moves
            while ptr:
                moves.append(ptr)
                ptr = ptr.next_sibling

            for move in moves:
                node.add_child(move)

    def backpropagate(self, node: SolverNode, result: EvaluationResult):
        current = node

        turn = 1
        if "W" in node:
            turn = -1
        while current:
            current.visit_count += 1
            current.winrate += result.score
            if current.child:
                if turn == 1:
                    children = current.child
                    for child in children:
                        if child.status == BoardState.BLACK_WIN:
                            current.status = BoardState.BLACK_WIN
                else:
                    children = current.child
                    for child in children:
                        if child.status == BoardState.WHITE_WIN:
                            current.status = BoardState.WHITE_WIN


            result.score = -result.score
            current = current.parent


class MCTS(Tree):

    def __init__(self):
        super().__init__()
        self.c = 1.41421356237

    def selection(self):
        xd = self.root
        while xd.num_children > 0:
            np = xd.visit_count 
            ch = xd.child 
            id = 0
            mxid = -1
            mxval = -1e18
            while ch:
                if ch.visit_count == 0:
                    nowscore = 1e18
                else:
                    nowscore = ch.winrate / ch.visit_count + self.c * math.sqrt(math.log(np) / ch.visit_count)
                
                if nowscore > mxval:
                    mxval = nowscore
                    mxid = id
                ch = ch.next_sibling
                id += 1
            xd = xd.get_child(mxid)
        
        return xd
