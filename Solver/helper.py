from __future__ import annotations

import typing

from .solver_node import SolverNode
from .types import BoardState


BLACK = "B"
WHITE = "W"
PLAYERS = (BLACK, WHITE)

WIN_STATE_BY_PLAYER = {
    BLACK: BoardState.BLACK_WIN,
    WHITE: BoardState.WHITE_WIN,
}


def opponent(player: str) -> str:
    if player == BLACK:
        return WHITE
    if player == WHITE:
        return BLACK
    raise ValueError(f"Unknown player: {player}")


def winning_state(player: str) -> BoardState:
    try:
        return WIN_STATE_BY_PLAYER[player]
    except KeyError as exc:
        raise ValueError(f"Unknown player: {player}") from exc


def player_of(node: SolverNode) -> str:
    for player in PLAYERS:
        if player in node:
            return player
    raise ValueError("Node does not contain a black or white move.")


def has_player(node: SolverNode, player: str) -> bool:
    if player not in PLAYERS:
        raise ValueError(f"Unknown player: {player}")
    return player in node


def is_black_move(node: SolverNode) -> bool:
    return has_player(node, BLACK)


def is_white_move(node: SolverNode) -> bool:
    return has_player(node, WHITE)


def first_child(node: SolverNode | None) -> SolverNode | None:
    return node.child if node else None


def response_node(node: SolverNode | None) -> SolverNode | None:
    return node.get_child(0) if node else None


def previous_turn_node(node: SolverNode | None) -> SolverNode | None:
    if node is None or node.parent is None:
        return None
    return node.parent.parent


def parent_turn_node(node: SolverNode | None, root: SolverNode | None = None) -> SolverNode | None:
    if node is None:
        return None
    if root is not None and node.parent is root:
        return root
    return previous_turn_node(node)


def iter_siblings(first: SolverNode | None) -> typing.Iterator[SolverNode]:
    current = first
    while current is not None:
        yield current
        current = current.next_sibling


def iter_children(node: SolverNode | None) -> typing.Iterator[SolverNode]:
    if node is None:
        return
    yield from iter_siblings(node.child)


def iter_turn_children(node: SolverNode | None) -> typing.Iterator[tuple[SolverNode, SolverNode | None]]:
    for first_move in iter_children(node):
        yield first_move, response_node(first_move)


def iter_response_children(node: SolverNode | None) -> typing.Iterator[SolverNode]:
    for _, reply in iter_turn_children(node):
        if reply is not None:
            yield reply


def has_response(node: SolverNode | None) -> bool:
    return response_node(node) is not None


def is_initial_engine_line(node: SolverNode, root: SolverNode | None = None) -> bool:
    if root is not None and node is root:
        return False
    reply = response_node(node)
    return node.id == 0 and reply is not None and reply.id == 0


def any_response_has_state(node: SolverNode | None, state: BoardState) -> bool:
    return any(reply.status == state for reply in iter_response_children(node))


def all_responses_are_solved(node: SolverNode | None) -> bool:
    replies = list(iter_response_children(node))
    if not replies:
        return False
    return all(reply.status != BoardState.UNKNOWN for reply in replies)


def first_response_status(node: SolverNode | None) -> BoardState:
    reply = next(iter_response_children(node), None)
    return reply.status if reply is not None else BoardState.UNKNOWN
