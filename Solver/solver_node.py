import sgf_tool
from .types import BoardState


class SolverNode(sgf_tool.SGFNode):

    def __init__(self):
        super().__init__()
        self.winrate: float = 0.0
        self.visit_count: int = 0
        self.status: BoardState = BoardState.UNKNOWN
        self.id: int = 0


class SolverNodeAllocator(sgf_tool.parser.NodeAllocator[SolverNode]):

    def allocate(self) -> SolverNode:
        return SolverNode()
