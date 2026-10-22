#!/bin/sh
# Demo: boot fin-blog on a fresh port, run a curl session, shut down.
# Usage: sh examples/demo.sh   (run from the repo root; build first with
# the finc command in README.md)
set -eu
cd "$(dirname "$0")/.."
PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
./fin-blog example/content "$PORT" "Demo Blog" &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1
echo "== index =="
curl -s "localhost:$PORT/" | grep -o '<a href="[^"]*"' | head -5
echo "== post =="
curl -s "localhost:$PORT/post/hello-fin-blog" | grep -o '<h1>[^<]*</h1>' | head -2
echo "== api =="
curl -s "localhost:$PORT/api/posts"; echo
echo "== static =="
curl -s "localhost:$PORT/static/style.css" | head -2
echo "== missing =="
curl -s -o /dev/null -w "%{http_code}\n" "localhost:$PORT/post/nope"
