# Changelog — fin-blog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] — 2026-10-22

### Added
- Markdown blog engine over HTTP: zhttp server + fin-markdown rendering
  + fin-template layouts + finson JSON meta API, in one binary.
- Routes: `GET /` (index, newest first), `GET /post/<slug>`,
  `GET /static/<name>` (text-only, traversal-blocked),
  `GET /api/posts` (JSON), 404 HTML / 404 JSON, 405 for non-GET.
- Front-matter posts (`title:`/`date:`), slug-fallback titles, built-in
  default layout when `layout.html` is missing, date-sorted index.
- Full lifecycle: README, `tests/smoke.py` (**35/35 SMOKE OK** over real
  HTTP), `examples/demo.sh` curl session, GitHub Actions CI,
  real-format `finn.toml`, MIT license, `example/` demo site (3 posts).
- Two real bugs found and fixed by executing (not review): freeing a
  string-literal default layout (segfault at startup) and storing a
  layout that aliased a freed `read_to_string` buffer (use-after-free) —
  both fixed with `clone()`; see NOTES.md.
