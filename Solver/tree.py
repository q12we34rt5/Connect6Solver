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

    def selection(self):
        pass

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

    def backpropagate(self, node: SolverNode):
        current = node
        while current:
            self.update_node_status(current)
            current = current.parent

    def update_node_status(self, node: SolverNode):
        if node.num_children == 0:
            return

        # # Determine turn based on children's moves
        # # If children have 'B' property, it means it was Black's turn at 'node'
        # # If children have 'W' property, it means it was White's turn at 'node'
        # first_child = node.child
        # if not first_child:
        #     return

        # is_black_turn = False
        # if "B" in first_child:
        #     is_black_turn = True
        # elif "W" in first_child:
        #     is_black_turn = False
        # else:
        #     # Should not happen in valid game tree
        #     return

        ###

        
        children = list(node.get_children_iter())

        if is_black_turn:
            # Black's turn:
            # Black wins if there exists a move leading to Black win (OR)
            # White wins if ALL moves lead to White win (AND)
            if any(child.status == BoardState.BLACK_WIN for child in children):
                node.status = BoardState.BLACK_WIN
            elif all(child.status == BoardState.WHITE_WIN for child in children):
                node.status = BoardState.WHITE_WIN
        else:
            # White's turn:
            # White wins if there exists a move leading to White win (OR)
            # Black wins if ALL moves lead to Black win (AND)
            if any(child.status == BoardState.WHITE_WIN for child in children):
                node.status = BoardState.WHITE_WIN
            elif all(child.status == BoardState.BLACK_WIN for child in children):
                node.status = BoardState.BLACK_WIN


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
                nowscore = ch.winrate / ch.visit_count + self.c * math.sqrt(math.log(np) / ch.visit_count)
                if nowscore > mxval:
                    mxval = nowscore
                    mxid = id
                ch = ch.next_sibling
                id += 1
            xd = xd.get_child(mxid)
        
        return xd
