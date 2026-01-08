# type: ignore
import sgf_tool
from Solver.solver_node import SolverNode, SolverNodeAllocator
from Solver.utils import (
    execute_nctu6,
    execute_nctu6_async,
    get_player,
    node_to_move_string,
    node_to_job,
    parse_nctu6_output,
    result_to_winrate,
    to_board_string
)

# input_sgf = ";B[JJ];W[IH];W[HI];B[KK];B[LJ];W[GJ];W[JG];B[AA];B[BB]"
input_sgf = ";B[JJ];W[LH];W[HH];B[JI];B[KJ]"

# parse the SGF into a tree structure
root = sgf_tool.SGFParser(node_allocator=SolverNodeAllocator()).parse(f"({input_sgf})")

# navigate to the leaf node
leaf = root
while leaf.num_children > 0:
    leaf = leaf.get_child(0)

# print the current board state
# print(to_board_string(leaf))

# dispatch leaf node to NCTU6
print("Calling NCTU6 with the arguments:")
print(f"-playtsumego {node_to_job(leaf)}")
output = execute_nctu6(
    ["-playtsumego", node_to_job(leaf)])

# print the NCTU6 output
print("NCTU6 output:")
print(output.strip())

# parse the NCTU6 output
result, move_nodes, comments = parse_nctu6_output(output)
# store ignore_str here because move_nodes will be modified later
ignore_str = move_nodes.to_sgf(root=False)
print("Result:", result)
print("SGF Nodes:", ignore_str)
print("Comments:", comments)
print("================")

# store winrate to move_nodes and add to tree
winrate = result_to_winrate(comments[0])
move_nodes.get_child(0)["WR"] = [str(winrate)]
leaf.add_child(move_nodes)

# dispatch leaf node to NCTU6 again with -ignore
print("Calling NCTU6 again with the arguments:")
print(f"-playtsumego {node_to_job(leaf)} -ignore {ignore_str}")
output = execute_nctu6(
    ["-playtsumego", node_to_job(leaf), "-ignore", ignore_str])

# print the NCTU6 output
print(f"NCTU6 output with -ignore {ignore_str}")
print(output.strip())

# parse the NCTU6 output
result, move_nodes, comments = parse_nctu6_output(output)
# store ignore_str here because move_nodes will be modified later
ignore_str = move_nodes.to_sgf(root=False)
print("Result:", result)
print("SGF Nodes:", ignore_str)
print("Comments:", comments)
print("================")

# store winrate to move_nodes and add to tree
winrate = result_to_winrate(comments[0])
move_nodes.get_child(0)["WR"] = [str(winrate)]
leaf.add_child(move_nodes)

# print the final SGF tree
print("Final SGF tree:")
print(root.to_sgf())