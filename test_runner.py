import subprocess
import time
import os
import signal

# Configurable packet loss and corruption for testing
LOSS_PROB = 0.2
CORRUPT_PROB = 0.2

def run_server():
    # Start server process
    return subprocess.Popen([
        "python", "reliable_udp_http.py", "server",
        "--loss", str(LOSS_PROB),
        "--corrupt", str(CORRUPT_PROB)
    ])

def run_client():
    time.sleep(2)  # Ensure server is ready
    subprocess.run([
        "python", "reliable_udp_http.py", "client",
        "--loss", str(LOSS_PROB),
        "--corrupt", str(CORRUPT_PROB)
    ])

if __name__ == "__main__":
    try:
        server_proc = run_server()
        run_client()
    finally:
        # Ensure server process is killed and socket is released
        if server_proc.poll() is None:
            print("[INFO] Terminating server process...")
            if os.name == 'nt':  # Windows
                server_proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:  # Linux/macOS
                server_proc.terminate()
            server_proc.wait()
        print("[INFO] Server terminated. Waiting for port cleanup...")
        time.sleep(1)  # Let OS fully release port
