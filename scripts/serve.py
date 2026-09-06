#!/usr/bin/env python3
"""Preview only the dist directory beside this script on localhost."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit


class DistHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        # SimpleHTTPRequestHandler follows symlinks; refuse anything outside dist.
        target = Path(self.translate_path(self.path)).resolve()
        root = Path(self.directory).resolve()
        request_parts = unquote(urlsplit(self.path).path).split("/")
        if root not in target.parents and target != root or ".." in request_parts:
            self.send_error(403, "Path outside dist")
            return None
        if target.is_dir():
            for name in ("index.html", "index.htm"):
                index = target / name
                if index.exists() and root not in index.resolve().parents:
                    self.send_error(403, "Path outside dist")
                    return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4190)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    dist = Path(__file__).resolve().parent / "dist"
    if dist.is_symlink() or not dist.is_dir() or not (dist / "index.html").is_file():
        print("serve: dist/index.html is missing or dist is a symlink. Build the exported project first with node build.mjs.", file=sys.stderr)
        return 1
    handler = partial(DistHandler, directory=str(dist))
    try:
        with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"Preview: http://127.0.0.1:{args.port}/ (dist only)", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except OSError as error:
        print(f"serve: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
