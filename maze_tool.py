#!/usr/bin/env python3
"""
maze_tool.py
Generate a maze-like grid (N,E,S,W = 1=open, 0=wall) and export to JSON.
"""

import json
import random
import time
import argparse
import sys
import os
from typing import List, Dict
from collections import deque

# ----------------------------------------------------------------------
# Python version check (secrets added in 3.6)
if sys.version_info < (3, 6):
    raise RuntimeError("Python >= 3.6 is required (for secrets module)")

try:
    import secrets
except ImportError:  # fallback (should not happen on 3.6+)
    import os
    secrets = None

# ---------------- Maze generator (iterative DFS backtracker) -------
DX = [0, 1, 0, -1]   # N, E, S, W
DY = [-1, 0, 1, 0]


def generate_maze(width: int, height: int, seed: int = None) -> List[Dict]:
    """Return a list of cell dicts: {'position':[x,y], 'directions':[N,E,S,W]}"""
    if seed is not None:
        random.seed(seed)

    grid = [[None for _ in range(width)] for _ in range(height)]

    def make_cell(x: int, y: int) -> Dict:
        return {"position": [x, y], "directions": [0, 0, 0, 0]}

    # start at (0,0) – deterministic
    sx, sy = 0, 0
    grid[sy][sx] = make_cell(sx, sy)
    stack: List[tuple[int, int]] = [(sx, sy)]

    while stack:
        x, y = stack[-1]
        neighbors = []
        for d in range(4):
            nx = x + DX[d]
            ny = y + DY[d]
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] is None:
                neighbors.append(d)

        if not neighbors:
            stack.pop()
            continue

        d = random.choice(neighbors)
        nx = x + DX[d]
        ny = y + DY[d]

        grid[ny][nx] = make_cell(nx, ny)
        # carve passage
        grid[y][x]["directions"][d] = 1
        grid[ny][nx]["directions"][(d + 2) % 4] = 1

        stack.append((nx, ny))

    # Flatten (defensive – every cell should exist)
    cells = []
    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            if cell is None:                     # should never happen
                cell = make_cell(x, y)
            cells.append(cell)
    return cells

def add_loops(cells: List[Dict], width: int, height: int, loop_factor: float) -> None:
    """Add loops by randomly removing walls between adjacent cells."""
    total_loops = int(width * height * loop_factor)
    grid = [[None for _ in range(width)] for _ in range(height)]
    for cell in cells:
        x, y = cell["position"]
        grid[y][x] = cell

    attempts = 0
    max_attempts = total_loops * 10  # prevent infinite loops if no walls to remove
    loops_added = 0

    while loops_added < total_loops and attempts < max_attempts:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        cell = grid[y][x]
        # Find neighbors that are adjacent but not connected (wall between)
        candidates = []
        for d in range(4):
            nx = x + DX[d]
            ny = y + DY[d]
            if 0 <= nx < width and 0 <= ny < height:
                neighbor = grid[ny][nx]
                if cell["directions"][d] == 0:
                    candidates.append(d)
        if candidates:
            d = random.choice(candidates)
            nx = x + DX[d]
            ny = y + DY[d]
            neighbor = grid[ny][nx]
            # Remove wall between cell and neighbor
            cell["directions"][d] = 1
            neighbor["directions"][(d + 2) % 4] = 1
            loops_added += 1
        attempts += 1


def find_farthest_cell(cells: List[Dict], width: int, height: int, start: tuple[int, int]) -> tuple[int, int]:
    """Find the farthest cell from start using BFS."""
    grid = [[None for _ in range(width)] for _ in range(height)]
    for cell in cells:
        x, y = cell["position"]
        grid[y][x] = cell

    visited = [[False for _ in range(width)] for _ in range(height)]
    queue = deque()
    queue.append((start[0], start[1], 0))  # x, y, distance
    visited[start[1]][start[0]] = True

    farthest_cell = start
    max_dist = 0

    while queue:
        x, y, dist = queue.popleft()
        if dist > max_dist:
            max_dist = dist
            farthest_cell = (x, y)

        cell = grid[y][x]
        for d in range(4):
            if cell["directions"][d] == 1:
                nx = x + DX[d]
                ny = y + DY[d]
                if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                    visited[ny][nx] = True
                    queue.append((nx, ny, dist + 1))

    return farthest_cell


# ---------------- JSON formatting helpers ---------------------------
def export_compact_lines(data: Dict) -> str:
    """Custom compact format: one cell per line, readable JSON."""
    lines = []
    lines.append("{")
    lines.append(f'  "width": {data["width"]},')
    lines.append(f'  "height": {data["height"]},')
    lines.append('  "cells": [')

    for i, cell in enumerate(data["cells"]):
        pos = cell["position"]
        dirs = cell["directions"]
        comma = "," if i < len(data["cells"]) - 1 else ""
        line = f'    {{ "position": [{pos[0]}, {pos[1]}], "directions": [{", ".join(map(str, dirs))}] }}{comma}'
        lines.append(line)

    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines)


def export_maze_html(maze: Dict, filename: str) -> None:
    width = maze["width"]
    height = maze["height"]
    cells = maze["cells"]

    # Build a 2D array for quick access: cells[y][x]
    grid = [[None for _ in range(width)] for _ in range(height)]
    for cell in cells:
        x, y = cell["position"]
        grid[y][x] = cell

    cell_size = 20
    wall_thickness = 2
    svg_width = width * cell_size + wall_thickness
    svg_height = height * cell_size + wall_thickness

    def line(x1, y1, x2, y2):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="{wall_thickness}"/>'

    svg_lines = []
    # Draw outer border
    svg_lines.append(line(0, 0, svg_width, 0))  # top
    svg_lines.append(line(0, 0, 0, svg_height))  # left
    svg_lines.append(line(svg_width, 0, svg_width, svg_height))  # right
    svg_lines.append(line(0, svg_height, svg_width, svg_height))  # bottom

    # Draw walls inside maze
    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            px = x * cell_size
            py = y * cell_size
            dirs = cell["directions"]
            # North wall
            if dirs[0] == 0:
                svg_lines.append(line(px, py, px + cell_size, py))
            # East wall
            if dirs[1] == 0:
                svg_lines.append(line(px + cell_size, py, px + cell_size, py + cell_size))
            # South wall
            if dirs[2] == 0:
                svg_lines.append(line(px, py + cell_size, px + cell_size, py + cell_size))
            # West wall
            if dirs[3] == 0:
                svg_lines.append(line(px, py, px, py + cell_size))

    # Add circles for start and end positions
    start = maze.get("start", (0, 0))
    end = maze.get("end", (width - 1, height - 1))
    cx_start = start[0] * cell_size + cell_size / 2
    cy_start = start[1] * cell_size + cell_size / 2
    cx_end = end[0] * cell_size + cell_size / 2
    cy_end = end[1] * cell_size + cell_size / 2
    radius = cell_size / 4
    svg_lines.append(f'<circle cx="{cx_start}" cy="{cy_start}" r="{radius}" fill="green" />')
    svg_lines.append(f'<circle cx="{cx_end}" cy="{cy_end}" r="{radius}" fill="red" />')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Maze {width}x{height}</title>
</head>
<body>
<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" style="background:#fff">
{chr(10).join(svg_lines)}
</svg>
</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)


def render_maze_grid(maze: Dict, start: tuple[int, int], end: tuple[int, int]) -> None:
    width = maze["width"]
    height = maze["height"]
    cells = maze["cells"]

    # Build a 2D array for quick access: cells[y][x]
    grid = [[None for _ in range(width)] for _ in range(height)]
    for cell in cells:
        x, y = cell["position"]
        grid[y][x] = cell

    # Print top border
    top_line = "+"
    for x in range(width):
        top_line += "---+"
    print(top_line)

    for y in range(height):
        # For each row, print the vertical walls and spaces
        line_vert = "|"
        line_horz = "+"

        for x in range(width):
            cell = grid[y][x]
            # Space inside cell
            if (x, y) == start:
                line_vert += " S "
            elif (x, y) == end:
                line_vert += " E "
            else:
                line_vert += "   "
            # East wall if no passage east
            if cell["directions"][1] == 1:
                line_vert += " "
            else:
                line_vert += "|"

        print(line_vert)

        for x in range(width):
            cell = grid[y][x]
            # South wall if no passage south
            if cell["directions"][2] == 1:
                line_horz += "   +"
            else:
                line_horz += "---+"
        print(line_horz)


# ----------------- CLI & main --------------------------------------
def build_data(width: int, height: int, seed: int = None, loops: float = 0.0, start_str: str = None, end_str: str = None) -> Dict:
    cells = generate_maze(width, height, seed)
    if loops > 0.0:
        add_loops(cells, width, height, loops)
    if start_str:
        start = tuple(map(int, start_str.split(',')))
    else:
        start = (0, 0)
    if end_str:
        end = tuple(map(int, end_str.split(',')))
    else:
        end = find_farthest_cell(cells, width, height, start)
    return {
        "width": width,
        "height": height,
        "cells": cells,
        "start": start,
        "end": end,
        "difficulty": {"loops": loops}
    }


def gen_random_id() -> str:
    if secrets:
        return secrets.token_hex(4)
    # fallback
    return os.urandom(4).hex()


def write_file(text: str, filename: str) -> None:
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def parse_args():
    parser = argparse.ArgumentParser(description="Maze generator -> JSON exporter")
    parser.add_argument("-w", "--width", type=int, default=10, help="width (columns)")
    parser.add_argument("-H", "--height", type=int, default=10, help="height (rows)")  # đổi -h thành -H
    parser.add_argument("-s", "--seed", type=int, help="random seed (optional)")
    parser.add_argument("-o", "--outdir", default=".", help="output directory")
    parser.add_argument("--loops", type=float, default=0.0, help="loops difficulty factor")
    parser.add_argument("--start", type=str, help="start position x,y")
    parser.add_argument("--end", type=str, help="end position x,y")
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    width = max(1, args.width)
    height = max(1, args.height)

    data = build_data(width, height, args.seed, args.loops, args.start, args.end)

    json_text = export_compact_lines(data)

    random_id = gen_random_id()
    timestamp = int(time.time())
    fname = f"matrix_{width}x{height}_{random_id}_{timestamp}.json"
    out_path = os.path.join(args.outdir.rstrip("/"), fname)

    write_file(json_text, out_path)
    print(f"Saved: {out_path}")

    html_path = out_path.rsplit('.', 1)[0] + ".html"
    export_maze_html(data, html_path)
    print(f"Saved: {html_path}")

    render_maze_grid(data, data["start"], data["end"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted by user")
    except Exception as e:
        sys.exit(f"Error: {e}")