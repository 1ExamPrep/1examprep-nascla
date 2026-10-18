"""Blog posts for build.py. No third-party packages.

Posts live in content/posts/<slug>.md:

    ---
    title: How to pick the right NEC edition for your exam
    date: 2026-10-16
    author: Pass Your Electrician Exam
    excerpt: One or two sentences shown on the blog index and in search results.
    image: https://cdn.shopify.com/.../cover.jpg
    tags: nec, journeyman, texas
    takeaways: First sentence | Second sentence | Third sentence   (optional; shown in the Key takeaways box)
    state: Texas          (optional: links the post to /texas/...)
    level: Journeyman     (optional)
    status: published     (or draft: kept out of the build)
    kind: page            (optional: a standalone page at /pages/<slug>/ instead of a blog post)
    metaTitle / metaDescription   (optional: used for <title> and the meta description)
    ---
    Markdown or HTML body.

The dashboard webhook writes these files; you can also write them by hand.
"""
import os, re, html, datetime

def parse_front(text):
    meta, body = {}, text
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1); meta[k.strip().lower()] = v.strip().strip('"').strip("'")
        body = text[m.end():]
    return meta, body.strip()

def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:80] or "post"

# --- small markdown converter: headings, paragraphs, lists, quotes, code, links, images, emphasis, hr, tables ---
def _inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", s)
    return s

def md_to_html(md):
    if re.match(r"^\s*<(p|h[1-6]|div|ul|ol|section|article|figure|blockquote|table)\b", md, re.I):
        return md  # already HTML
    lines = md.replace("\r\n", "\n").split("\n"); out = []; i = 0
    def flush_para(buf):
        if buf: out.append("<p>%s</p>" % _inline(" ".join(x.strip() for x in buf)))
    buf = []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            flush_para(buf); buf = []; code = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"): code.append(lines[i]); i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(code))); i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            flush_para(buf); buf = []; lvl = min(max(len(m.group(1)), 2), 4)  # '#' and '##' become h2 (h1 is the title), '###' h3
            txt = m.group(2).strip().rstrip("#").strip(); out.append('<h%d id="%s">%s</h%d>' % (lvl, slugify(txt), _inline(txt), lvl)); i += 1; continue
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", ln): flush_para(buf); buf = []; out.append("<hr>"); i += 1; continue
        if re.match(r"^\s*[-*+]\s+", ln) or re.match(r"^\s*\d+[.)]\s+", ln):
            flush_para(buf); buf = []; ordered = bool(re.match(r"^\s*\d+[.)]\s+", ln)); items = []
            while i < len(lines) and (re.match(r"^\s*[-*+]\s+", lines[i]) or re.match(r"^\s*\d+[.)]\s+", lines[i])):
                items.append(re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", lines[i])); i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]): items[-1] += " " + lines[i].strip(); i += 1
            out.append("<%s>%s</%s>" % ("ol" if ordered else "ul", "".join("<li>%s</li>" % _inline(x) for x in items), "ol" if ordered else "ul")); continue
        if ln.startswith(">"):
            flush_para(buf); buf = []; q = []
            while i < len(lines) and lines[i].startswith(">"): q.append(lines[i][1:].strip()); i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % _inline(" ".join(q))); continue
        if "|" in ln and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush_para(buf); buf = []; rows = []
            while i < len(lines) and "|" in lines[i]: rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            head, body = rows[0], rows[2:]
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % ("".join("<th>%s</th>" % _inline(c) for c in head), "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c) for c in r) for r in body))); continue
        if ln.strip().startswith("<") and ln.strip().endswith(">"):
            flush_para(buf); buf = []; out.append(ln.strip()); i += 1; continue
        if not ln.strip(): flush_para(buf); buf = []; i += 1; continue
        buf.append(ln); i += 1
    flush_para(buf)
    return "\n".join(out)

def load_posts(folder, site_url=""):
    posts = []
    if not os.path.isdir(folder): return posts
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".md"): continue
        meta, body = parse_front(open(os.path.join(folder, fn), encoding="utf-8").read())
        if meta.get("status", "published").lower() == "draft": continue
        slug = slugify(meta.get("slug") or fn[:-3])
        date = (meta.get("date") or datetime.date.fromtimestamp(os.path.getmtime(os.path.join(folder, fn))).isoformat())[:10]
        body_html = md_to_html(body)
        text = re.sub(r"<[^>]+>", " ", body_html); text = re.sub(r"\s+", " ", html.unescape(text)).strip()
        excerpt = meta.get("excerpt") or (text[:157].rsplit(" ", 1)[0] + "…" if len(text) > 160 else text)
        img = meta.get("image") or (re.search(r'<img[^>]+src="([^"]+)"', body_html) or [None, ""])[1]
        if img.startswith("/") and site_url: img = site_url.rstrip("/") + img
        excerpt = re.sub(r"^summary\s*:?\s*", "", excerpt, flags=re.I) if excerpt else excerpt
        tags = [t.strip() for t in re.split(r"[,;]", meta.get("tags", "")) if t.strip()]
        takeaways = [t.strip() for t in meta.get("takeaways", "").split("|") if t.strip()]
        if not takeaways:  # a "Key takeaways" list inside the post wins over guessing
            km = re.search(r"<h[2-4][^>]*>\s*key\s+takeaways?\s*</h[2-4]>\s*(?:<p[^>]*>.*?</p>\s*)?<[uo]l[^>]*>(.*?)</[uo]l>", body_html, re.S | re.I)
            if km: takeaways = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", li))).strip() for li in re.findall(r"<li[^>]*>(.*?)</li>", km.group(1), re.S)]
        if not takeaways:  # first sentence of the first three sections
            for sec in re.split(r"<h2[^>]*>.*?</h2>", body_html, flags=re.S)[1:4]:
                st = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", sec))).strip()
                m = re.match(r"(.{25,220}?[.!?])(\s|$)", st)
                if m: takeaways.append(m.group(1))
        posts.append({"slug": slug, "title": meta.get("title") or slug.replace("-", " ").title(), "date": date, "updated": (meta.get("updated") or date)[:10],
                      "kind": (meta.get("kind") or "blog").lower(), "meta_title": meta.get("metatitle", ""), "meta_description": meta.get("metadescription", ""), "external_id": meta.get("externalid", ""),
                      "author": meta.get("author") or "", "excerpt": excerpt, "image": img, "tags": tags, "state": meta.get("state", ""), "level": meta.get("level", ""),
                      "takeaways": takeaways[:4], "html": body_html, "words": len(text.split()), "file": fn})
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts
