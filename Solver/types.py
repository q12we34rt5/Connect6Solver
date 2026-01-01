import enum
from dataclasses import dataclass
import typing

if typing.TYPE_CHECKING:
    from .solver_node import SolverNode


class BoardState(enum.Enum):
    UNKNOWN = -1
    BLACK_WIN = 0
    WHITE_WIN = 1


@dataclass
class EvaluationResult:
    moves: "SolverNode"
    score: float
    state: BoardState
    info: dict
    raw: str
