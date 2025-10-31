import subprocess, sys, os

script_path = os.path.join(os.path.dirname(__file__), "app_streamlit_maze.py")

try:
    subprocess.Popen(["streamlit", "run", script_path])
    input("Press Enter to quit the app...\n")
except Exception as e:
    print("Error:", e)
    input("Press Enter to exit...\n")
