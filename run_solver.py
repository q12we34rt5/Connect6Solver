import sys
import os

# Ensure we can import from local directories
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Solver.solver import Solver
from Solver.types import BoardState
from Solver.utils import node_to_move_string, to_board_string

def main():
    # Example SGF: 
    # Black places one stone at JJ.
    # White places two stones at IH, HI.
    # Black places two stones at KK, LJ.
    # Now it is White's turn to move.
    input_sgf = "(;B[JJ];W[IH];W[HI];B[KK];B[LJ])"
    
    print(f"Initializing solver with job: {input_sgf}")
    
    solver = Solver()
    solver.set_job(input_sgf)
    
    # Run simulations
    # You can increase this number for better results
    simulations = 100
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
    
    # Traverse to the end of the input SGF to see next move predictions
    # Count moves in SGF (simple heuristic: count ';')
    input_moves_count = input_sgf.count(";")
    print(f"\nTraversing {input_moves_count} steps to reach the end of input sequence...")
    
    current = root
    # Follow the main line (first child) which corresponds to the initial SGF sequence
    for i in range(input_moves_count):
        if current.num_children > 0:
            current = current.get_child(0)
        else:
            print(f"Stopped early at depth {i}")
            break
            
    print(f"Current Board State (at leaf):")
    # print(to_board_string(current)) # Optional: print board at leaf

    print("\nCandidate Moves (Children of Leaf):")
    child = root.get_child(0)
    best_child = None
    max_visits = -1

    while child:
        move_str = node_to_move_string(child)
        avg_score = child.winrate / child.visit_count if child.visit_count > 0 else 0
        
        print(f"Move: {move_str:<10} | Visits: {child.visit_count:<5} | Score: {avg_score:>.2f} | Status: {child.status}")
        
        if child.visit_count > max_visits:
            max_visits = child.visit_count
            best_child = child
            
        child = child.next_sibling

    if best_child:
        print("\n" + "=" * 40)
        best_move_str = node_to_move_string(best_child)
        print(f"Best Move: {best_move_str} with {max_visits} visits.")
        # print("Board State after Best Move:")
        # print(to_board_string(best_child))
    else:
        print("\nNo valid moves found.")

if __name__ == "__main__":
    main()
