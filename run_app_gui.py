import os
import threading
import time
import subprocess
import webview
import socket
import sys


# --- Global ---
current_port = 8501


# --- Helper: Check port availability ---
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


# --- Run Streamlit server ---
def run_streamlit():
    """
    Run Streamlit server using Python interpreter from venv inside bundle (if frozen),
    or normal sys.executable if running from source.
    """
    global current_port

    base_dir = os.path.abspath(os.path.dirname(__file__))

    # Nếu chạy trong PyInstaller bundle
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", base_dir)
        venv_python = os.path.join(base_dir, "venv_app/bin/python3")
        if os.path.exists(venv_python):
            python_exec = venv_python
        else:
            # fallback: dùng Python hệ thống
            python_exec = "/usr/bin/python3"
    else:
        python_exec = sys.executable

    # Kiểm tra file Streamlit script
    script_path = os.path.join(base_dir, "app_streamlit_maze.py")
    if not os.path.exists(script_path):
        print(f"❌ Không tìm thấy file: {script_path}")
        return

    # Chọn port trống
    port = current_port
    while is_port_in_use(port):
        port += 1
    current_port = port

    print(f"🚀 Running Streamlit on port {port} using {python_exec}")

    # Chạy Streamlit server
    subprocess.Popen(
        [
            python_exec, "-m", "streamlit", "run",
            script_path,
            "--server.port", str(port),
            "--server.headless", "true",
            "--server.fileWatcherType", "none"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# --- GUI controller ---
def start_main_app(window):
    """Run inside webview.start() main loop"""
    def delayed_launch():
        time.sleep(2)

        # Đợi server Streamlit sẵn sàng
        for _ in range(60):
            if is_port_in_use(current_port):
                break
            time.sleep(0.5)
        else:
            print("❌ Streamlit server not ready.")
            window.load_html("<h3>Failed to start Maze Generator</h3>")
            return

        # Đóng splash và mở app chính
        webview.windows[0].load_url(f"http://localhost:{current_port}")

    threading.Thread(target=delayed_launch, daemon=True).start()


# --- Main ---
if __name__ == "__main__":
    # Chạy Streamlit nền
    threading.Thread(target=run_streamlit, daemon=True).start()

    # Splash window
    splash_html = """
<html>
<body style="margin:0;background:#0a0a0a;color:#00ff99;font-family:monospace;overflow:hidden;">
  <div style="display:flex;justify-content:center;align-items:center;height:100vh;">
    <div style="text-align:center">
        <img src="https://raw.githubusercontent.com/google/material-design-icons/refs/heads/master/png/image/auto_awesome/materialicons/48dp/2x/baseline_auto_awesome_black_48dp.png" width="96">
        <h2>Loading Maze Generator...</h2>
    </div>
  </div>
</body>
</html>
"""

    splash = webview.create_window(
    "Maze Generator",
    html=splash_html,
    width=1200,
    height=800,
    resizable=False,
    frameless=True,        # ✅ Không khung, không nút back
    easy_drag=False,       # ✅ Tắt gesture drag (ẩn back)
    text_select=False      # ✅ Không highlight text khi kéo
    )

    # Run webview with splash, then load main app
    webview.start(start_main_app, splash)