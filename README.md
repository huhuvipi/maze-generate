# 🌀 Maze Generator Tool (Python + Streamlit + WebView)

**Maze Generator** is a visualization and utility tool that procedurally generates mazes using Python.  
It allows users to configure size, difficulty, and export the maze data as a JSON file.  
The app is built with **Streamlit** for the UI and wrapped inside a **desktop WebView (macOS)** launcher.

> ⚠️ Note: The macOS `.app` packaging process is still being refined — the web version works fully functional.

---

## 🚀 Features

- **Random Maze Generation**  
  Generates a fully randomized maze using a **Depth-First Search (DFS)** / **Backtracking** algorithm.

- **Configurable Maze Size**  
  Input custom width and height to create any grid dimension.

- **Difficulty Control**  
  Adjusts wall removal randomness to make the maze easier or harder.

- **Start / End Points**  
  Automatically assigns random **Start (🟢)** and **End (🔴)** cells in the maze.

- **JSON Export**  
  Save the maze as a JSON file with the following format:
  ```json
  {
    "width": 10,
    "height": 13,
    "cells": [
      { "position": [0, 0], "directions": [1, 1, 0, 0] },
      { "position": [1, 0], "directions": [1, 1, 0, 1] },
      ...
    ],
    "start": [0, 0],
    "end": [9, 12]
  }
  ```

- **Web Visualization**  
  Interactive grid-based display rendered in Streamlit with start/end color indicators.

- **Desktop Launcher (WebView + Splash)**  
  Includes a `run_app_gui.py` launcher that shows a splash screen and opens a Streamlit WebView app window (for macOS desktop use).

---

## 🧩 Project Structure

```
MazeGenerator/
├── app_streamlit_maze.py      # Streamlit web app UI
├── run_app_gui.py             # Desktop launcher (WebView + splash)
├── venv_app/                  # Embedded Python venv (used for macOS build)
├── splash.png                 # Splash screen image
├── Icon.icns                  # macOS app icon
└── dist/                      # Build output (.app, .dmg)
```

---

## ⚙️ How to Run (Development Mode)

### 1️⃣ Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2️⃣ Install dependencies
```bash
pip install streamlit pywebview
```

### 3️⃣ Run the Streamlit app directly
```bash
streamlit run app_streamlit_maze.py
```

### 4️⃣ Or launch via the WebView app
```bash
python run_app_gui.py
```

---

## 💻 macOS App Packaging (In Progress)

To bundle as a standalone `.app`:
```bash
pyinstaller --noconsole --windowed   --icon=Icon.icns   --add-data "app_streamlit_maze.py:."   --add-data "splash.png:."   --add-data "venv_app:venv_app"   --name "Maze Generator" run_app_gui.py
```

> Make sure `venv_app` contains `streamlit` and `pywebview` installed before building.

The splash screen and UI will appear as expected,  
but **Streamlit startup inside `.app` is still being optimized** (currently works perfectly via terminal).

---

## 🧠 Tech Stack

- **Python 3.11+**
- **Streamlit** – web-based UI rendering
- **PyWebView** – desktop wrapper
- **DFS / Backtracking** – maze generation algorithm
- **JSON** – exportable maze data structure

---

## 🧭 Future Improvements

- ✅ Stable macOS `.app` packaging  
- ✅ Import existing JSON mazes  
- 🔲 Real-time maze solving visualization  
- 🔲 Multi-platform builds (Windows / Linux)  
- 🔲 Switchable render modes (grid / path view)

---

## 👨‍💻 Author

Developed collaboratively by **Vinh Huynh**  
with AI-assisted architecture and debugging support from ChatGPT (GPT-5).

---

> “Every maze has a path — you just need to generate it.” 🌀
