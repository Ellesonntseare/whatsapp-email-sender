#!/usr/bin/env python3
"""Serve the bundled game on this computer and open its browser."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import webbrowser


def main():
    folder = Path(__file__).resolve().parent
    handler = partial(SimpleHTTPRequestHandler, directory=str(folder))
    for port in range(8000, 8011):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            continue
    else:
        raise SystemExit("Ports 8000–8010 are busy. Open index.html directly to play.")
    url = f"http://localhost:{port}"
    print(f"Crownfall is running at {url}\nPress Ctrl+C to stop.", flush=True)
    opener = threading.Timer(0.5, webbrowser.open, args=(url,))
    opener.daemon = True
    opener.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
