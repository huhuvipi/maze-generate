
# app_streamlit_maze.py
import streamlit as st
import json, random, time, os, secrets
from collections import deque
from typing import List, Dict, Tuple

st.set_page_config(page_title="Maze Generator", layout="wide")

st.set_page_config(initial_sidebar_state="expanded") # You can set this to "collapsed" if you want the sidebar hidden on initial load

# Inject CSS to hide the collapse/expand button
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] {
        display: none
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Maze Generator Controls")
st.sidebar.write("Use the controls below to generate and customize mazes.")

st.title("Maze Generator Tool")
st.write("This tool generates mazes using the Recursive Backtracker algorithm with optional loops. You can customize the maze size, loop factor, seed, start/end points, and download the maze in various formats.")

# Directions: N=0, E=1, S=2, W=3
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]

# ---------------- core maze functions ----------------
def generate_maze(width: int, height: int, seed: int = None) -> List[Dict]:
    if seed is not None:
        random.seed(seed)
    grid = [[None for _ in range(width)] for _ in range(height)]
    def make_cell(x, y):
        return {"position":[x,y], "directions":[0,0,0,0]}
    sx, sy = 0, 0
    grid[sy][sx] = make_cell(sx, sy)
    stack = [(sx, sy)]
    while stack:
        x, y = stack[-1]
        neighbors = []
        for d in range(4):
            nx, ny = x + DX[d], y + DY[d]
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] is None:
                neighbors.append(d)
        if not neighbors:
            stack.pop()
            continue
        d = random.choice(neighbors)
        nx, ny = x + DX[d], y + DY[d]
        grid[ny][nx] = make_cell(nx, ny)
        grid[y][x]["directions"][d] = 1
        grid[ny][nx]["directions"][(d+2)%4] = 1
        stack.append((nx, ny))
    cells = []
    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            if cell is None:
                cell = make_cell(x, y)
            cells.append(cell)
    return cells

def add_loops(cells: List[Dict], width: int, height: int, loop_factor: float) -> None:
    total_loops = int(width * height * loop_factor)
    grid = [[None for _ in range(width)] for _ in range(height)]
    for c in cells:
        x,y = c["position"]
        grid[y][x] = c
    attempts, loops_added = 0, 0
    max_attempts = max(1000, total_loops * 10)
    while loops_added < total_loops and attempts < max_attempts:
        x = random.randrange(width)
        y = random.randrange(height)
        cell = grid[y][x]
        candidates = []
        for d in range(4):
            nx, ny = x + DX[d], y + DY[d]
            if 0 <= nx < width and 0 <= ny < height:
                if cell["directions"][d] == 0:
                    candidates.append(d)
        if candidates:
            d = random.choice(candidates)
            nx, ny = x + DX[d], y + DY[d]
            neighbor = grid[ny][nx]
            # make passage
            cell["directions"][d] = 1
            neighbor["directions"][(d+2)%4] = 1
            loops_added += 1
        attempts += 1

def find_farthest_cell(cells: List[Dict], width: int, height: int, start: Tuple[int,int]) -> Tuple[int,int]:
    grid = [[None for _ in range(width)] for _ in range(height)]
    for c in cells:
        x,y = c["position"]
        grid[y][x] = c
    visited = [[False]*width for _ in range(height)]
    q = deque()
    q.append((start[0], start[1], 0))
    visited[start[1]][start[0]] = True
    farthest = start
    maxd = 0
    while q:
        x,y,d = q.popleft()
        if d > maxd:
            maxd = d
            farthest = (x,y)
        cell = grid[y][x]
        for dir in range(4):
            if cell["directions"][dir] == 1:
                nx, ny = x + DX[dir], y + DY[dir]
                if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                    visited[ny][nx] = True
                    q.append((nx, ny, d+1))
    return farthest

# ---------------- exporters / renderers ----------------
def export_compact_lines(data: Dict) -> str:
    lines = []
    lines.append("{")
    lines.append(f'  "width": {data["width"]},')
    lines.append(f'  "height": {data["height"]},')
    # add start/end/difficulty if present
    if "start" in data:
        sx, sy = data["start"]
        lines.append(f'  "start": [{sx}, {sy}],')
    if "end" in data:
        ex, ey = data["end"]
        lines.append(f'  "end": [{ex}, {ey}],')
    lines.append('  "cells": [')
    for i, cell in enumerate(data["cells"]):
        pos = cell["position"]
        dirs = cell["directions"]
        comma = "," if i < len(data["cells"]) - 1 else ""
        lines.append(f'    {{ "position": [{pos[0]}, {pos[1]}], "directions": [{", ".join(map(str, dirs))}] }}{comma}')
    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines)

def render_ascii_grid(maze: Dict, start: Tuple[int,int], end: Tuple[int,int]) -> str:
    width = maze["width"]; height = maze["height"]
    grid = [[None for _ in range(width)] for _ in range(height)]
    for c in maze["cells"]:
        x,y = c["position"]; grid[y][x] = c
    out_lines = []
    out_lines.append("+" + "---+"*width)
    for y in range(height):
        line_vert = "|"
        for x in range(width):
            if (x,y) == start:
                cell_content = " S "
            elif (x,y) == end:
                cell_content = " E "
            else:
                cell_content = "   "
            cell = grid[y][x]
            if cell["directions"][1] == 1:
                line_vert += cell_content + " "
            else:
                line_vert += cell_content + "|"
        out_lines.append(line_vert)
        line_h = "+"
        for x in range(width):
            cell = grid[y][x]
            if cell["directions"][2] == 1:
                line_h += "   +"
            else:
                line_h += "---+"
        out_lines.append(line_h)
    return "\n".join(out_lines)

def export_html_svg(maze: Dict, start: Tuple[int,int], end: Tuple[int,int], cell_size:int=24) -> str:
    width = maze["width"]; height = maze["height"]
    grid = [[None for _ in range(width)] for _ in range(height)]
    for c in maze["cells"]:
        x,y = c["position"]; grid[y][x] = c
    wall = 2
    w = width * cell_size + wall
    h = height * cell_size + wall
    def line(x1,y1,x2,y2):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="{wall}" />'
    svg = []
    svg.append(f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" style="background:#fff">')
    # outer border
    svg.append(line(0,0,w,0)); svg.append(line(0,0,0,h)); svg.append(line(w,0,w,h)); svg.append(line(0,h,w,h))
    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            px = x*cell_size; py = y*cell_size
            dirs = cell["directions"]
            if dirs[0] == 0: svg.append(line(px, py, px+cell_size, py))
            if dirs[1] == 0: svg.append(line(px+cell_size, py, px+cell_size, py+cell_size))
            if dirs[2] == 0: svg.append(line(px, py+cell_size, px+cell_size, py+cell_size))
            if dirs[3] == 0: svg.append(line(px, py, px, py+cell_size))
    # start / end dots
    sx, sy = start; ex, ey = end
    cx = sx*cell_size + cell_size/2; cy = sy*cell_size + cell_size/2
    ex_c = ex*cell_size + cell_size/2; ey_c = ey*cell_size + cell_size/2
    r = cell_size/4
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="green" />')
    svg.append(f'<circle cx="{ex_c}" cy="{ey_c}" r="{r}" fill="red" />')
    svg.append("</svg>")
    html = "<!doctype html><html><meta charset='utf-8'><body>" + "\n".join(svg) + "</body></html>"
    return html

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Maze Tool", layout="wide")
st.title("Maze generator tool (Streamlit)")

# Sidebar inputs
with st.sidebar.form("controls"):
    st.header("Parameters")
    width = st.number_input("Width (columns)", min_value=1, max_value=200, value=10)
    height = st.number_input("Height (rows)", min_value=1, max_value=200, value=10)
    loops = st.slider("Loop factor (0.0 = perfect)", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
    seed = st.text_input("Seed (optional, int)", value="")
    start_text = st.text_input("Start (x,y) or empty for (0,0)", value="")
    end_text = st.text_input("End (x,y) or empty for farthest", value="")
    filename_prefix = st.text_input("Filename prefix", value="matrix")
    pretty = st.checkbox("Show pretty JSON preview (compact-lines exported to file)", value=True)
    submitted = st.form_submit_button("Generate")

# stateful storage (simple)
if "last_maze" not in st.session_state: st.session_state["last_maze"] = None

if submitted:
    s = int(seed) if seed.strip() and seed.strip().lstrip("-").isdigit() else None
    cells = generate_maze(width, height, s)
    if loops and loops > 0:
        add_loops(cells, width, height, loops)
    if start_text.strip():
        sx, sy = tuple(map(int, start_text.split(",")))
        start = (sx, sy)
    else:
        start = (0,0)
    if end_text.strip():
        ex, ey = tuple(map(int, end_text.split(",")))
        end = (ex, ey)
    else:
        end = find_farthest_cell(cells, width, height, start)
    data = {
        "width": width, "height": height, "cells": cells,
        "start": start, "end": end, "difficulty": {"loops": loops}
    }
    st.session_state["last_maze"] = data
    st.success(f"Generated {width}x{height} maze. start={start} end={end}")

# If there is a maze, show previews and export buttons
data = st.session_state.get("last_maze")
col1, col2 = st.columns([1,1])
if data:
    # JSON text (compact-lines)
    json_text = export_compact_lines(data)
    # ASCII
    ascii_text = render_ascii_grid(data, data["start"], data["end"])
    # HTML/SVG
    html_text = export_html_svg(data, data["start"], data["end"])

    with col1:
        st.subheader("Maze SVG preview")
        st.markdown("Start = green, End = red")
        st.components.v1.html(html_text, height=400)

        st.download_button("Download HTML", data=html_text, file_name=f"{filename_prefix}_{width}x{height}_{secrets.token_hex(4)}.html", mime="text/html")
        st.download_button("Download JSON", data=json_text, file_name=f"{filename_prefix}_{width}x{height}_{secrets.token_hex(4)}.json", mime="application/json")

    with col2:
        st.subheader("ASCII grid")
        st.code(ascii_text, language=None)
        st.subheader("JSON (compact one cell per line)")
        if pretty:
            st.text_area("JSON preview", json_text, height=300)
        else:
            st.text_area("JSON preview (minified)", json_text.replace("\n",""), height=300)

else:
    st.info("Set parameters in the left panel and press Generate.")
