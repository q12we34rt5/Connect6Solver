import sys
import os
import argparse

# Ensure we can import from local directories
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Solver.solver import Solver
from Solver.types import BoardState
from Solver.utils import node_to_move_string, to_board_string
import sgf_tool
from Solver.solver_node import SolverNode, SolverNodeAllocator

def save_tree(simulation_id, root):
    for node, _ in sgf_tool.utils.Algorithm.dfs_iterator(root):
        winrate = node.winrate / node.visit_count if node.visit_count > 0 else 0
        node["C"] = [
            f"winrate = {winrate:.2f}\n"
            f"visit_count = {node.visit_count}\n"
            f"status = {node.status}\n"
            f"id = {node.id}\n"
        ]

    with open(output_file, "w") as f:
        f.write(root.to_sgf())
def dfs(node, dep):
    # print(f"we are children, and our dep:{dep}")

    while node:
        move_str = node_to_move_string(node)
        move_str2 = node_to_move_string(node.get_child(0))
        node.get_child(0).status = node.status
        node.get_child(0).visit_count = node.visit_count
        node.get_child(0).winrate = node.winrate
        node.get_child(0).id = node.id
        
        # avg_score = node.winrate / node.visit_count if node.visit_count > 0 else 0
        # print(f"Move: {move_str}{move_str2} | Visits: {node.visit_count:<5} | Score: {avg_score:>.2f} | Status: {node.status}")
        hehe = node.child.child
        if not hehe:
            node = node.next_sibling
            continue
        dfs(hehe, dep + 1)
        node = node.next_sibling 

    # print("go up to parent")


def main():
    # Example SGF: 
    # Black places one stone at JJ.
    # White places two stones at IH, HI.
    # Black places two stones at KK, LJ.
    # Now it is White's turn to move.
    
    parser = argparse.ArgumentParser(description="Connect6 Solver")
    parser.add_argument("--sgf", type=str, default="(;B[JJ];W[LH];W[HH];B[JI];B[KJ])", help="Input SGF string")
    parser.add_argument("--simulations", type=int, default=2, help="Number of simulations to run")
    parser.add_argument("--output", type=str, default="result_2.sgf", help="Output SGF filename")
    args = parser.parse_args()

    input_sgf = args.sgf
    simulations = args.simulations
    output_file = args.output
    
    print(f"Initializing solver with job: {input_sgf}")
    
    solver = Solver("/mnt/nfs/work/q12we34rt5/NCTU6/NCTU6")
    # solver = Solver()
    solver.set_job(input_sgf)
    
    # Run simulations
    print(f"Running {simulations} simulations...")
    solver.solve(simulations=simulations)
    
    root = solver.tree.root
    if not root:
        print("Error: Root is None!")
        return

    dfs(root.get_child(0), 0)
    print("=" * 40)
    print(f"Root Status: {root.status}")
    print(f"Root Visit Count: {root.visit_count}")
    print(f"Root Winrate (Accumulated): {root.winrate / root.visit_count}")
    print("=" * 40)
    
    for node, _ in sgf_tool.utils.Algorithm.dfs_iterator(root):
        winrate = node.winrate / node.visit_count if node.visit_count > 0 else 0
        node["C"] = [
            f"winrate = {winrate:.2f}\n"
            f"visit_count = {node.visit_count}\n"
            f"status = {node.status}\n"
            f"id = {node.id}\n"
        ]

    with open(output_file, "w") as f:
        f.write(root.to_sgf())
    print(f"SGF saved to {output_file}")

    # dfs(root.get_child(0), 1)

if __name__ == "__main__":
    main()
