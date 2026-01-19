import sys
import os

# Ensure we can import from local directories
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Solver.solver import Solver
from Solver.types import BoardState
from Solver.utils import node_to_move_string, to_board_string
import sgf_tool
from Solver.solver_node import SolverNode, SolverNodeAllocator



def dfs(node, dep):
    print(f"we are children, and our dep:{dep}")

    while node:
        move_str = node_to_move_string(node)
        move_str2 = node_to_move_string(node.get_child(0))
        avg_score = node.winrate / node.visit_count if node.visit_count > 0 else 0
        
        print(f"Move: {move_str}{move_str2} | Visits: {node.visit_count:<5} | Score: {avg_score:>.2f} | Status: {node.status}")
        hehe = node.child.child
        if not hehe:
            node = node.next_sibling
            continue
        dfs(hehe, dep + 1)
        node = node.next_sibling 

    print("go up to parent")



def main():
    # Example SGF: 
    # Black places one stone at JJ.
    # White places two stones at IH, HI.
    # Black places two stones at KK, LJ.
    # Now it is White's turn to move.
    input_sgf = "(;B[JJ];W[LH];W[HH];B[JI];B[KJ])"
    
    print(f"Initializing solver with job: {input_sgf}")
    
    solver = Solver()
    solver.set_job(input_sgf)
    
    # Run simulations
    simulations = 2
    print(f"Running {simulations} simulations...")
    solver.solve(simulations=simulations)
    
    root = solver.tree.root
    if not root:
        print("Error: Root is None!")
        return

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

    with open("result.sgf", "w") as f:
        f.write(root.to_sgf())
    print("SGF saved to result.sgf")

    # dfs(root.get_child(0), 1)

if __name__ == "__main__":
    main()
