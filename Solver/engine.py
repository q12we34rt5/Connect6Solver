import abc
import typing
from .solver_node import SolverNode
from .types import BoardState, EvaluationResult


class Engine(abc.ABC):
    @abc.abstractmethod
    def evaluate(self, node: SolverNode, **kwargs) -> EvaluationResult:
        pass

    @abc.abstractmethod
    async def evaluate_async(self, node: SolverNode, **kwargs) -> EvaluationResult:
        pass


class NCTU6Engine(Engine):
    def __init__(self, executable_path: typing.Optional[str] = None):
        self.executable_path = executable_path

    def _parse_result(self, output: str) -> EvaluationResult:
        from .utils import parse_nctu6_output, result_to_winrate

        result_str, move_nodes, comments = parse_nctu6_output(output)

        score = 0.0
        if comments:
            try:
                score = result_to_winrate(comments[0])
            except ValueError:
                pass

        state = BoardState.UNKNOWN
        if score == 1.0:
            state = BoardState.BLACK_WIN
        elif score == -1.0:
            state = BoardState.WHITE_WIN

        return EvaluationResult(
            moves=move_nodes,
            score=score,
            state=state,
            info={"result": result_str, "comments": comments},
            raw=output
        )

    def evaluate(self, node: SolverNode, **kwargs) -> EvaluationResult:
        from .utils import execute_nctu6, node_to_job

        job = node_to_job(node)
        args = ["-playtsumego", job]

        if "ignore" in kwargs:
            args.extend(["-ignore", kwargs["ignore"]])

        if self.executable_path:
            output = execute_nctu6(args, executable=self.executable_path)
        else:
            output = execute_nctu6(args)

        return self._parse_result(output)

    async def evaluate_async(self, node: SolverNode, **kwargs) -> EvaluationResult:
        from .utils import execute_nctu6_async, node_to_job

        job = node_to_job(node)
        args = ["-playtsumego", job]

        if "ignore" in kwargs:
            args.extend(["-ignore", kwargs["ignore"]])

        if self.executable_path:
            output = await execute_nctu6_async(args, executable=self.executable_path)
        else:
            output = await execute_nctu6_async(args)

        return self._parse_result(output)
