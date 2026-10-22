# fin-blog — a markdown blog engine served over HTTP, in Fin

The "full-stack" Fin demo: it composes four independently built and
verified libraries into one binary — **zhttp** (server), **fin-markdown**
(post rendering), **fin-template** (layout), **finson** (JSON meta API).
Posts are Markdown files with fin-ssg-style front matter, loaded once at
startup and rendered once; requests serve the stored HTML.

## Routes

| Route | Result |
|---|---|
| `GET /` | Index: post list, newest first by date (undated posts last) |
| `GET /post/<slug>` | Post page (404 HTML when the slug is unknown) |
| `GET /static/<name>` | Text file from `<content>/static/` (`.css` `.js` `.html` `.txt` only; flat names — no `/` or `..`) |
| `GET /api/posts` | JSON `[{slug, title, date}, ...]` (newest first) |
| anything else | 404 HTML (404 JSON under `/api/*`) |

Only `GET` is served; other methods get 405. The server never aborts on
a request — bad client input gets a 4xx page.

## Content layout

```
content/
  layout.html          # fin-template layout ({{site_title}} {{title}}
                       # {{date}} {{content}}); missing -> built-in default
  posts/
    hello.md           # --- front matter: title: / date: --- then Markdown
    plain-note.md      # no front matter -> title falls back to the slug
  static/
    style.css          # served at /static/style.css
```

Layout rendering uses fin-template's `tpl_render` shim: `{{title}}` and
`{{date}}` are auto-escaped, `{{content}}` passes through `|safe` — so
fin-blog passes RAW titles/dates and pre-rendered HTML bodies. (fin-ssg
pre-escapes titles before `tpl_render` and double-escapes them; fin-blog
does not.)

## Build

```sh
finc -I <zhttp>/src -I <fin-template>/src -I <fin-markdown>/src \
     -I <finson>/src src/main.fin -o fin-blog
```

Library checkouts are sibling repos (`M1778/zhttp`, `M1778/fin-template`,
`M1778/fin-markdown`, `M1778/finson`) until `finn` publishes them.

## Run

```sh
./fin-blog [content_dir] [port] [site_title]
# defaults: content, 8080, "My Fin Blog"
./fin-blog example/content 8080 "Smoke Blog"
```

## Test

```sh
python3 tests/smoke.py   # builds fin-blog, boots it on a fresh port,
                         # drives every route over real HTTP (35 checks)
```

Dep dirs for the smoke build come from `FIN_ZHTTP`, `FIN_TEMPLATE`,
`FIN_MARKDOWN`, `FINSON` (defaults: the fin-dev workspace siblings);
`FINC` overrides the compiler binary.

## Known limits (v0.1.0)

- In-memory, single-threaded accept loop (same model as fin-rest-todo);
  no per-connection concurrency yet.
- Flat post directory (no subdirectories); post cap 256.
- Static files are text-only (no binary assets — `read_to_string`).
- Dates sort lexicographically: use ISO `YYYY-MM-DD` dates.
- stdlib caveat, inherited from every Fin server: `Socket::serve` lacks
  `SO_REUSEADDR`, so restarting on the SAME port within ~60s of serving
  a client fails to bind — the smoke test uses a fresh port per run.

## License

MIT — see `LICENSE`.
