import argparse
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sgf_tool
from Solver.async_solver import AsyncSolver, MAX_CONCURRENT_NCTU6
from Solver.utils import node_to_move_string


DEFAULT_EXECUTABLE = "/mnt/nfs/work/q12we34rt5/NCTU6/NCTU6"


def copy_stats_to_response_nodes(node, dep):
    while node:
        response = node.get_child(0)
        if response is None:
            node = node.next_sibling
            continue

        response.status = node.status
        response.visit_count = node.visit_count
        response.winrate = node.winrate
        response.id = node.id

        next_turn = node.child.child if node.child and node.child.child else None
        if next_turn:
            copy_stats_to_response_nodes(next_turn, dep + 1)
        node = node.next_sibling


async def async_main():
    parser = argparse.ArgumentParser(description="Async Connect6 Solver")
    parser.add_argument("--sgf", type=str, default="(;B[JJ];W[LH];W[HH];B[JI];B[KJ])", help="Input SGF string")
    parser.add_argument("--simulations", type=int, default=2, help="Number of selection rounds to run")
    parser.add_argument("--concurrency", type=int, default=MAX_CONCURRENT_NCTU6, help=f"Maximum number of concurrent NCTU6 evaluations, capped at {MAX_CONCURRENT_NCTU6}")
    parser.add_argument("--output", type=str, default="async_result.sgf", help="Output SGF filename")
    parser.add_argument("--executable", type=str, default=DEFAULT_EXECUTABLE, help="Path to the NCTU6 executable")
    parser.add_argument("--virtual-loss-weight", type=float, default=1.0, help="Penalty applied per in-flight visit")
    args = parser.parse_args()

    print(f"Initializing async solver with job: {args.sgf}")
    solver = AsyncSolver(args.executable, virtual_loss_weight=args.virtual_loss_weight)
    solver.set_job(args.sgf)

    print(f"Running {args.simulations} simulations with concurrency={args.concurrency}...")
    processed = await solver.solve_async(simulations=args.simulations, concurrency=args.concurrency)

    root = solver.tree.root
    if not root:
        print("Error: Root is None!")
        return

    first_child = root.get_child(0)
    if first_child:
        copy_stats_to_response_nodes(first_child, 0)

    print("=" * 40)
    print(f"Root Status: {root.status}")
    print(f"Root Visit Count: {root.visit_count}")
    root_winrate = root.winrate / root.visit_count if root.visit_count > 0 else 0
    print(f"Root Winrate (Accumulated): {root_winrate}")
    print(f"Processed Evaluations: {processed}")
    print("=" * 40)

    for node, _ in sgf_tool.utils.Algorithm.dfs_iterator(root):
        winrate = node.winrate / node.visit_count if node.visit_count > 0 else 0
        virtual_loss = getattr(node, "virtual_loss_count", 0)
        node["C"] = [
            f"winrate = {winrate:.2f}\n"
            f"visit_count = {node.visit_count}\n"
            f"status = {node.status}\n"
            f"id = {node.id}\n"
            f"virtual_loss = {virtual_loss}\n"
        ]

    with open(args.output, "w") as f:
        f.write(root.to_sgf())
    print(f"SGF saved to {args.output}")

    # Give asyncio subprocess transports one final loop tick to close pipes cleanly.
    await asyncio.sleep(0.1)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
