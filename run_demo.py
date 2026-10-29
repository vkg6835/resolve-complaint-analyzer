"""One-command local demo. Internet and an API key are not required."""
import argparse
import os
from pathlib import Path
import socket
import threading
import webbrowser

os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("OMP_NUM_THREADS", "4")
ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not (ROOT / "artifacts" / "evaluation.json").exists():
        raise SystemExit("Training artifacts are missing. Run scripts/prepare_data.py and scripts/train.py first.")
    url = f"http://127.0.0.1:{args.port}"
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            import urllib.request
            try:
                with urllib.request.urlopen(url + "/api/health", timeout=2) as response:
                    import json
                    already_running = json.load(response).get("local_only") is True
            except Exception:
                already_running = False
            if already_running:
                print(f"Resolve is already running at {url}")
                if not args.no_browser:
                    webbrowser.open(url)
                return
            raise SystemExit(f"Port {args.port} is in use. Try --port 8001.")
    if not args.no_browser:
        timer = threading.Timer(2.5, lambda: webbrowser.open(url))
        timer.daemon = True
        timer.start()
    import uvicorn
    print(f"Resolve demo: {url}\nPress Ctrl+C to stop.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, reload=False)


if __name__ == "__main__":
    main()
