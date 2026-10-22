---
title: Hello, Fin Blog
date: 2026-10-22
---
This is the first post of the example blog. It exercises the **full
rendering pipeline**: front matter, headings, `inline code`, and a link.

- Markdown in, HTML out — via **fin-markdown**
- Layout via **fin-template**
- Served over HTTP by **zhttp**

```fin
fun main() <noret> {
    println_str("hello from fin-blog");
}
```

Read more in [the second post](/post/second-post) — or check the
[JSON index](/api/posts).
