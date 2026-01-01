import sgf_tool
from .solver_node import SolverNode, SolverNodeAllocator
import subprocess
import os
import asyncio
import typing


def execute_nctu6(command_args, *, executable=f"{os.path.dirname(os.path.abspath(__file__))}/../NCTU6/exec", working_dir=None):
    """Execute the NCTU6 executable with given command arguments.

    Args:
        command_args (list): List of command line arguments to pass to the executable.
        executable (str): Path to the NCTU6 executable.
        working_dir (str): Directory to run the executable in. If None, defaults to the directory of the executable.
    Returns:
        str: The standard output from the command execution.
    Raises:
        FileNotFoundError: If the executable or working directory is not found.
        RuntimeError: If any other error occurs during execution.
    """

    # Define the working directory where the executable is located
    # This is important to ensure the NCTU6 (exec) program runs correctly
    if working_dir is None:
        working_dir = os.path.dirname(os.path.abspath(executable))
    command = [executable] + command_args

    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        return result.stdout

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Could not find the executable or directory. Checked in: {working_dir}") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}") from e


async def execute_nctu6_async(command_args, *, executable=f"{os.path.dirname(os.path.abspath(__file__))}/../NCTU6/exec", working_dir=None):
    """Execute the NCTU6 executable asynchronously with given command arguments.

    Args:
        command_args (list): List of command line arguments to pass to the executable.
        executable (str): Path to the NCTU6 executable.
        working_dir (str): Directory to run the executable in. If None, defaults to the directory of the executable.
    Returns:
        str: The standard output from the command execution.
    Raises:
        FileNotFoundError: If the executable or working directory is not found.
        RuntimeError: If any other error occurs during execution.
    """

    # Define the working directory where the executable is located
    # This is important to ensure the NCTU6 (exec) program runs correctly
    if working_dir is None:
        working_dir = os.path.dirname(os.path.abspath(executable))

    try:
        process = await asyncio.create_subprocess_exec(
            executable,
            *command_args,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        return stdout.decode('utf-8')

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Could not find the executable or directory. Checked in: {working_dir}") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}") from e


def get_player(node: sgf_tool.SGFNode) -> str:
    if "B" in node:
        return "B"
    elif "W" in node:
        return "W"
    else:
        raise ValueError("Node does not contain a move.")


def node_to_move_string(node: sgf_tool.SGFNode) -> str:
    player = get_player(node)
    move_coords = node[player][0]
    move_str = f"{player}[{move_coords}]"
    return move_str


def node_to_job(node: sgf_tool.SGFNode) -> str:
    nodes = []
    ptr = node
    while ptr:
        if ptr:
            nodes.append(ptr)
        ptr = ptr.get_parent()
    nodes.reverse()
    job = ";" + ";".join(node_to_move_string(n) for n in nodes)
    return job


def parse_nctu6_output(output: str) -> typing.Tuple[str, SolverNode, typing.List[str]]:
    result, remainder = output.split(" ", 1)
    sgf_string = remainder[:12]
    move_nodes = sgf_tool.SGFParser(
        node_allocator=SolverNodeAllocator()).parse(f"({sgf_string})")
    comments = remainder[12:].split("];C[")
    comments[0] = comments[0][3:]
    comments[-1] = comments[-1].strip()[:-1]
    return result, move_nodes, comments


def result_to_winrate(result: str) -> float:
    MAPPING = {
        "B:w": 1,
        "B:a_w": 0.9,
        "a-b:B3": 0.7,
        "a-b:B2": 0.5,
        "a-b:B1": 0.3,
        "a-b:stable": 0,
        "a-b:unstable": 0,
        "a-b:w1": -0.3,
        "a-b:w2": -0.5,
        "a-b:w3": -0.7,
        "W:a_w": -0.9,
        "W:w": -1
    }
    if result not in MAPPING:
        raise ValueError(f"Unknown result format: {result}")
    return MAPPING[result]


def to_board_string(node: sgf_tool.SGFNode, board_size: int = 19) -> str:
    class TextType:
        NORMAL = 0
        BOLD = 1
        UNDERLINE = 4
        SIZE = 3

    class TextColor:
        BLACK = 0
        RED = 1
        GREEN = 2
        YELLOW = 3
        BLUE = 4
        PURPLE = 5
        CYAN = 6
        WHITE = 7
        SIZE = 8

    def get_color_text(text: str, text_type: int, text_color: int, text_background: int) -> str:
        text_type_number = {
            TextType.NORMAL: 0,
            TextType.BOLD: 1,
            TextType.UNDERLINE: 4
        }
        return f"\033[{text_type_number.get(text_type, 0)};3{text_color};4{text_background}m{text}\033[0m"

    # replay moves
    nodes = []
    ptr = node
    while ptr:
        nodes.append(ptr)
        ptr = ptr.get_parent()
    nodes.reverse()

    grid = {}  # (row, col) -> TextColor (BLACK or WHITE)
    all_moves = []  # list of (row, col)

    for n in nodes:
        for color_key, color_enum in [("B", TextColor.BLACK), ("W", TextColor.WHITE)]:
            if color_key in n:
                for coords in n[color_key]:
                    if len(coords) != 2:
                        continue
                    # sgf coords: 'a' is 0. 'aa' is (0,0)
                    # we map SGF y=0 to row=board_size-1 (top)
                    c = ord(coords[0].lower()) - ord('a')
                    r_sgf = ord(coords[1].lower()) - ord('a')
                    r = board_size - 1 - r_sgf

                    if 0 <= r < board_size and 0 <= c < board_size:
                        grid[(r, c)] = color_enum
                        all_moves.append((r, c))

    last_move = all_moves[-1] if len(all_moves) >= 1 else None
    last2_move = all_moves[-2] if len(all_moves) >= 2 else None

    lines = []

    # coordinate string helper
    def get_coordinate_string():
        s = "  "
        for i in range(board_size):
            c_val = ord('A') + i
            # if c_val >= ord('I'):
            #     c_val += 1
            s += " " + chr(c_val)
        s += "   "
        return get_color_text(s, TextType.BOLD, TextColor.BLACK, TextColor.YELLOW)

    lines.append(get_coordinate_string())

    for row in range(board_size):
        # row label
        label = str(row + 1)
        if row + 1 < 10:
            label = " " + label

        line_parts = []
        line_parts.append(get_color_text(
            label, TextType.BOLD, TextColor.BLACK, TextColor.YELLOW))

        for col in range(board_size):
            pos = (row, col)
            stone_color = grid.get(pos)

            # determine symbol and color
            if stone_color == TextColor.BLACK:
                symbol = "O"
                color = TextColor.BLACK
            elif stone_color == TextColor.WHITE:
                symbol = "O"
                color = TextColor.WHITE
            else:
                symbol = "."
                color = TextColor.BLACK

            # determine prefix (marker or space)
            if pos == last_move:
                prefix = ">"
                prefix_type = TextType.BOLD
                prefix_color = TextColor.RED
            elif pos == last2_move:
                prefix = ">"
                prefix_type = TextType.NORMAL
                prefix_color = TextColor.RED
            else:
                prefix = " "
                prefix_type = TextType.BOLD
                prefix_color = color

            if pos == last_move or pos == last2_move:
                line_parts.append(get_color_text(
                    prefix, prefix_type, prefix_color, TextColor.YELLOW))
                line_parts.append(get_color_text(
                    symbol, TextType.BOLD, color, TextColor.YELLOW))
            else:
                line_parts.append(get_color_text(
                    prefix + symbol, TextType.BOLD, color, TextColor.YELLOW))

        # right side label
        label_right = " " + str(row + 1)
        if row + 1 < 10:
            label_right += " "
        line_parts.append(get_color_text(
            label_right, TextType.BOLD, TextColor.BLACK, TextColor.YELLOW))

        lines.append("".join(line_parts))

    lines.append(get_coordinate_string())

    return "\n".join(lines)
