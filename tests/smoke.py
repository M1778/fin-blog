#!/usr/bin/env python3
"""Smoke test for fin-blog: builds the binary (deps via env vars, see
below), boots it on a fresh port (fresh per run — see the SO_REUSEADDR
note in src/main.fin) against example/content, and drives every route
over real HTTP. Fails loudly.

Dep dirs (override with env vars; defaults are the fin-dev workspace
siblings, where the libraries live until Eleanor creates their repos):
  FIN_ZHTTP, FIN_TEMPLATE, FIN_MARKDOWN, FINSON
"""
import http.client
import json
import os
import socket
import subprocess
import sys
import time

passed = 0
failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL {name} {extra}")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
BIN = os.path.join(ROOT, "fin-blog")
CONTENT = os.path.join(ROOT, "example", "content")

WS = os.path.expanduser("~/workspace/fin-dev")
FINC = os.environ.get("FINC") or os.path.join(
    WS, "tester-1", "Fin", "build", "finc")
if not (os.path.isfile(FINC) and os.access(FINC, os.X_OK)):
    import shutil
    FINC = shutil.which("finc") or FINC
DEPS = {
    "FIN_ZHTTP": os.path.join(WS, "builder-1", "zhttp", "src"),
    "FIN_TEMPLATE": os.path.join(WS, "builder-2", "fin-template", "src"),
    "FIN_MARKDOWN": os.path.join(WS, "builder-3", "fin-markdown", "src"),
    "FINSON": os.path.join(WS, "builder-1", "finson", "src"),
}
includes = []
for var, default in DEPS.items():
    d = os.environ.get(var, default)
    if not os.path.isdir(d):
        print(f"missing dep dir for {var}: {d}")
        sys.exit(2)
    includes += ["-I", d]

print("== frontend check ==")
r = subprocess.run([FINC] + includes + [os.path.join(ROOT, "src", "main.fin")],
                   capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout, r.stderr)
    sys.exit(2)
print("== codegen + link ==")
r = subprocess.run([FINC] + includes +
                   [os.path.join(ROOT, "src", "main.fin"), "-o", BIN],
                   capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout, r.stderr)
    sys.exit(2)

PORT = free_port()
proc = subprocess.Popen([BIN, CONTENT, str(PORT), "Smoke Blog"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True)


def req(method, path):
    conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=5)
    conn.request(method, path)
    resp = conn.getresponse()
    raw = resp.read().decode()
    ctype = resp.getheader("Content-Type") or ""
    conn.close()
    return resp.status, ctype, raw


try:
    deadline = time.time() + 15
    while True:
        try:
            s = socket.create_connection(("127.0.0.1", PORT), timeout=1)
            s.close()
            break
        except OSError:
            if time.time() > deadline:
                print("server did not come up; output:")
                print(proc.stdout.read() if proc.stdout else "")
                sys.exit(2)
            time.sleep(0.2)
    # NOTE: the probe connection above sends no request; the server
    # replies 404 and moves on. The accept loop survives it (proven by
    # every request below passing).

    st, ct, body = req("GET", "/")
    check("index 200", st == 200, f"got {st}")
    check("index html type", "text/html" in ct, ct)
    check("index lists hello post", "/post/hello-fin-blog" in body)
    check("index lists second post", "/post/second-post" in body)
    check("index lists plain note", "/post/plain-note" in body)
    check("index newest first (dated posts first, undated last)",
          body.index("hello-fin-blog") < body.index("second-post") <
          body.index("plain-note"),
          "order wrong")
    check("index uses layout css link", "/static/style.css" in body)

    st, ct, body = req("GET", "/post/hello-fin-blog")
    check("post 200", st == 200, f"got {st}")
    check("post title in head", "<title>Hello, Fin Blog" in body)
    check("post h1 rendered exactly once",
          body.count("<h1>Hello, Fin Blog</h1>") == 1,
          f"count={body.count('<h1>Hello, Fin Blog</h1>')}")
    check("post bold rendered", "<strong>full" in body)
    check("post date rendered", "2026-10-22" in body)
    check("post fenced code rendered", "<pre><code" in body)

    st, _, body = req("GET", "/post/second-post")
    check("older post 200", st == 200, f"got {st}")
    check("older post date", "2026-10-20" in body)
    check("older post quote", "<blockquote>" in body)

    st, _, body = req("GET", "/post/plain-note")
    check("no-front-matter post 200", st == 200, f"got {st}")
    check("no-front-matter title falls back to slug",
          "<title>plain-note" in body, body[:400])

    st, _, body = req("GET", "/post/nope")
    check("unknown post 404", st == 404, f"got {st}")
    check("unknown post 404 page", "Not found" in body)

    st, _, body = req("GET", "/post/hello-fin-blog?x=1")
    check("query stripped", st == 200, f"got {st}")

    st, ct, body = req("GET", "/api/posts")
    check("api 200", st == 200, f"got {st}")
    check("api json type", "application/json" in ct, ct)
    data = json.loads(body)
    check("api 3 posts", len(data) == 3, f"got {data}")
    check("api newest first", data[0]["slug"] == "hello-fin-blog", f"{data}")
    check("api fields", data[1] == {"slug": "second-post",
                                    "title": "Second Post, Older Date",
                                    "date": "2026-10-20"}, f"{data[1]}")

    st, ct, body = req("GET", "/api/nope")
    check("api unknown 404 json", st == 404 and
          json.loads(body) == {"error": "not found"}, f"{st} {body}")

    st, ct, body = req("GET", "/static/style.css")
    check("static css 200", st == 200, f"got {st}")
    check("static css type", "text/css" in ct, ct)
    check("static css body", "max-width" in body)

    st, _, _ = req("GET", "/static/../main.fin")
    check("static traversal blocked", st == 404, f"got {st}")
    st, _, _ = req("GET", "/static/evil.exe")
    check("static bad extension 404", st == 404, f"got {st}")
    st, _, _ = req("GET", "/static/missing.css")
    check("static missing 404", st == 404, f"got {st}")

    st, _, body = req("GET", "/nope")
    check("unknown route 404 html", st == 404 and "Not found" in body,
          f"{st}")
    st, _, _ = req("POST", "/")
    check("non-GET 405", st == 405, f"got {st}")

    print(f"SMOKE {'OK' if failed == 0 else 'FAILED'}: "
          f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
