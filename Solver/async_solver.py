from __future__ import annotations

import asyncio
from dataclasses import dataclass
import math
import typing

from .engine import NCTU6Engine
from .helper import previous_turn_node
from .solver_node import SolverNode
from .tree import MCTS
from .types import BoardState, EvaluationResult
from .utils import node_to_move_string


MAX_CONCURRENT_NCTU6 = 32


@dataclass
class PendingEvaluation:
    node: SolverNode
    path: list[SolverNode]
    simulation_id: int
    label: str
    ignore: str | None = None


class AsyncSolver:
    def __init__(
        self,
        executable_path: typing.Optional[str] = None,
        *,
        virtual_loss_weight: float = 1.0,
    ):
        self.engine = NCTU6Engine(executable_path=executable_path)
        self.tree = MCTS()
        self.virtual_loss_weight = virtual_loss_weight

    def set_job(self, job: str):
        self.tree.load_sgf(job)

    def get_ignore_string(self, node: SolverNode) -> str:
        ignore_nodes = self.tree.collect_child_moves(node)
        return ','.join(
            ';' + ';'.join(node_to_move_string(move) for move in move_pair)
            for move_pair in ignore_nodes
        )

    def should_skip_evaluation(self, node: SolverNode | None) -> bool:
        if node is None or node.parent is None:
            return True
        return node.parent.id == 0 and node.child and node.child.id == 0

    def virtual_loss_count(self, node: SolverNode) -> int:
        return getattr(node, "virtual_loss_count", 0)

    def add_virtual_loss(self, path: list[SolverNode]):
        for node in path:
            node.virtual_loss_count = self.virtual_loss_count(node) + 1

    def remove_virtual_loss(self, path: list[SolverNode]):
        for node in path:
            node.virtual_loss_count = max(0, self.virtual_loss_count(node) - 1)

    def ucb_score(self, parent: SolverNode, child: SolverNode) -> float:
        if child.visit_count == 0 or parent.visit_count == 0:
            score = math.inf
        else:
            exploitation = child.winrate / child.visit_count
            if "W" in child:
                exploitation = -exploitation
            exploration = self.tree.c * math.sqrt(math.log(parent.visit_count) / child.visit_count)
            score = exploitation + exploration

        return score - self.virtual_loss_weight * self.virtual_loss_count(child)

    def select_best_child(self, node: SolverNode) -> SolverNode | None:
        child = node.child
        best_child = None
        best_score = -math.inf

        while child:
            if child.status == BoardState.UNKNOWN:
                score = self.ucb_score(node, child)
                if score > best_score:
                    best_score = score
                    best_child = child
            child = child.next_sibling

        return best_child

    def selection_path(self) -> tuple[SolverNode, list[SolverNode]]:
        node = self.tree.root
        path: list[SolverNode] = []

        while node and node.num_children > 0:
            selected = self.select_best_child(node)
            if selected is None:
                break

            path.append(selected)
            response = selected.get_child(0)
            if response is None:
                node = selected
                break

            path.append(response)
            node = response

        return node, path

    def path_until(self, path: list[SolverNode], target: SolverNode | None) -> list[SolverNode]:
        if target is None:
            return []
        for index, node in enumerate(path):
            if node is target:
                return path[:index + 1]
        return [target]

    def make_pending(
        self,
        node: SolverNode | None,
        path: list[SolverNode],
        simulation_id: int,
        label: str,
        in_flight_nodes: set[SolverNode],
    ) -> PendingEvaluation | None:
        if self.should_skip_evaluation(node):
            return None

        assert node is not None
        if node in in_flight_nodes:
            return None

        if node not in path:
            path = [*path, node]

        ignore = self.get_ignore_string(node) if node.num_children > 0 else None
        return PendingEvaluation(
            node=node,
            path=path,
            simulation_id=simulation_id,
            label=label,
            ignore=ignore,
        )

    async def evaluate_pending(self, pending: PendingEvaluation) -> EvaluationResult:
        if pending.ignore:
            return await self.engine.evaluate_async(pending.node, ignore=pending.ignore)
        return await self.engine.evaluate_async(pending.node)

    def apply_evaluation_result(self, pending: PendingEvaluation, result: EvaluationResult):
        self.tree.tree_expand(pending.node, result, pending.simulation_id)

        if result.moves:
            expanded = pending.node.get_child(pending.node.num_children - 1)
            expanded.status = result.state
            self.tree.backpropagate(expanded, result.score)
        else:
            pending.node.status = result.state
            self.tree.backpropagate(pending.node, result.score)

    def dispatch_request(
        self,
        pending: dict[asyncio.Task[EvaluationResult], PendingEvaluation],
        in_flight_nodes: set[SolverNode],
        request: PendingEvaluation,
    ):
        self.add_virtual_loss(request.path)
        task = asyncio.create_task(self.evaluate_pending(request))
        pending[task] = request
        in_flight_nodes.add(request.node)

    def create_evaluation_tasks(
        self,
        pending: dict[asyncio.Task[EvaluationResult], PendingEvaluation],
        in_flight_nodes: set[SolverNode],
        simulation_id: int,
        available_slots: int,
    ) -> bool:
        if available_slots <= 0:
            return False

        leaf, path = self.selection_path()
        request = self.make_pending(leaf, path, simulation_id, "leaf", in_flight_nodes)
        if request is None:
            return False

        self.dispatch_request(pending, in_flight_nodes, request)
        return True

    async def process_done_tasks(
        self,
        done: typing.Iterable[asyncio.Task[EvaluationResult]],
        pending: dict[asyncio.Task[EvaluationResult], PendingEvaluation],
        in_flight_nodes: set[SolverNode],
        concurrency: int,
    ) -> int:
        processed = 0
        for task in done:
            request = pending.pop(task)
            in_flight_nodes.discard(request.node)
            self.remove_virtual_loss(request.path)

            result = await task
            self.apply_evaluation_result(request, result)
            processed += 1
            print(
                f"finished simulation {request.simulation_id} {request.label}: "
                f"score={result.score:.2f} state={result.state}"
            )

            if request.label == "leaf" and request.node.id != 0 and len(pending) < concurrency:
                parent = previous_turn_node(request.node)
                parent_path = self.path_until(request.path, parent)
                parent_request = self.make_pending(
                    parent,
                    parent_path,
                    request.simulation_id,
                    "parent",
                    in_flight_nodes,
                )
                if parent_request:
                    self.dispatch_request(pending, in_flight_nodes, parent_request)
                    print(f"dispatch simulation {request.simulation_id}/parent")
        return processed

    async def solve_async(self, simulations: int = 100, concurrency: int = 2):
        if self.tree.root is None:
            raise ValueError("No job is set. Call set_job() before solve_async().")
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        concurrency = min(concurrency, MAX_CONCURRENT_NCTU6)

        pending: dict[asyncio.Task[EvaluationResult], PendingEvaluation] = {}
        in_flight_nodes: set[SolverNode] = set()
        submitted_simulations = 0
        processed_evaluations = 0
        no_selectable_node = False

        while (submitted_simulations < simulations and not no_selectable_node) or pending:
            if self.tree.root.status != BoardState.UNKNOWN:
                break

            ready = [task for task in pending if task.done()]
            if ready:
                processed_evaluations += await self.process_done_tasks(ready, pending, in_flight_nodes, concurrency)
                continue

            while submitted_simulations < simulations and len(pending) < concurrency:
                simulation_id = submitted_simulations + 1
                available_slots = concurrency - len(pending)
                created = self.create_evaluation_tasks(
                    pending,
                    in_flight_nodes,
                    simulation_id,
                    available_slots,
                )
                if not created:
                    if pending:
                        break
                    no_selectable_node = True
                    print("stop dispatching: no selectable leaf remains")
                    break

                submitted_simulations = simulation_id
                print(f"dispatch simulation {submitted_simulations}/{simulations}")

                ready = [task for task in pending if task.done()]
                if ready:
                    break

            ready = [task for task in pending if task.done()]
            if ready:
                processed_evaluations += await self.process_done_tasks(ready, pending, in_flight_nodes, concurrency)
                continue

            if pending:
                done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
                processed_evaluations += await self.process_done_tasks(done, pending, in_flight_nodes, concurrency)
            else:
                break

        for request in pending.values():
            in_flight_nodes.discard(request.node)
            self.remove_virtual_loss(request.path)

        for task in pending:
            task.cancel()

        if pending:
            await asyncio.gather(*pending.keys(), return_exceptions=True)

        return processed_evaluations
