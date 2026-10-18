#!/usr/bin/env python3
"""Turn Shopify product data into shared/catalog.js and store/products-full.json for the NASCLA site.

Input: a JSON list of products, either raw Admin GraphQL nodes (what tools/sync_shopify.py writes)
or the flattened records in data/shopify/nascla-products.json. Usage:

  python3 tools/build_catalog.py data/shopify/nascla-products.json

Every product is sorted three ways, all from its Shopify title and product type:
  state  : the state named in the title (None = nationwide)
  exam   : which NASCLA exam it prepares for (see EXAMS / exam_of)
  kind   : what sort of product it is (see KINDS / kind_of)
If a new product lands in the wrong place, adjust exam_of() or kind_of() here.

Prints "changed" or "unchanged" and exits 0 either way.
"""
import json, re, os, sys, datetime
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATES = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington","Washington DC","West Virginia","Wisconsin","Wyoming"]

# exam slug -> (display name, short name, sort order)
EXAMS = {
    "commercial-general-building-contractor": ("Commercial General Building Contractor", "Commercial GC", 1),
    "master-electrical-contractor": ("Master Electrical Contractor", "Master Electrical", 2),
    "journeyman-electrician": ("Journeyman Electrician", "Journeyman", 3),
    "residential-electrical-contractor": ("Residential Electrical Contractor", "Residential Electrical", 4),
    "business-and-law": ("Business and Law", "Business & Law", 5),
}

def exam_of(t):
    s = t.lower()
    if re.search(r"residential electric|\(r-11\)", s): return "residential-electrical-contractor"
    if "journey" in s: return "journeyman-electrician"
    if re.search(r"master electrical|master unlimited|electrical contractors? \(c-11\)|trade examination for electrical contractors", s): return "master-electrical-contractor"
    if re.search(r"guide to business|business, law|business and law|business & law|business, and project|business basic|landscape contractor|home improvement", s): return "business-and-law"
    if re.search(r"commercial|general building|general contractor|multi state application", s): return "commercial-general-building-contractor"
    return None

# kind slug -> (display name, rank). Rank orders packages on a listing page, smallest to most complete.
KINDS = {
    "tabs": ("Pre-Printed Tabs", 0), "flash-cards": ("Flash Cards", 0), "book": ("Book", 0),
    "practice-questions": ("Online Practice Questions", 1), "online-course": ("Online Exam Prep Course", 2),
    "complete-pass-package": ("Complete Pass Package", 3), "live-training": ("Live Virtual + Self-Study Training", 3),
    "book-package": ("Exam Book Package", 4), "highlighted-tabbed": ("Highlighted & Tabbed Book Package", 5),
    "rental": ("Books & Courses Rental Package", 6), "ultimate": ("Ultimate Exam Prep Rental Package", 7),
    "the-1-package": ("The 1 Package: All-Inclusive", 8), "application": ("Multi-State Application Bundle", 9),
}
BY_TYPE = {"Tabs": "tabs", "Book": "book", "Practice Course": "practice-questions", "Online Course": "online-course",
           "Business Complete Package": "complete-pass-package", "Live Training": "live-training", "Book Package": "book-package",
           "Book Package H/T": "highlighted-tabbed", "Book Rental": "rental", "Ultimate Package": "ultimate", "1 Package": "the-1-package",
           "Application": "application"}
PACKAGE_KINDS = {k for k, (n, r) in KINDS.items() if r > 0}

def kind_of(t, ptype):
    s = t.lower()
    if ptype in BY_TYPE: k = BY_TYPE[ptype]
    elif "flash card" in s: k = "flash-cards"
    elif "rental" in s: k = "rental"
    elif "tabs" in s: k = "tabs"
    else: k = "book"
    if k == "book-package" and "highlighted" in s: k = "highlighted-tabbed"
    if k == "book" and "flash card" in s and "guide" not in s: k = "flash-cards"
    return k

def ordinal_edition(t):
    m = re.search(r"(\d+)(st|nd|rd|th) edition", t, re.I)
    return ("%s%s Ed." % (m.group(1), m.group(2).lower())) if m else ""

def kind_name(k, t):
    """display name for one product. Books and tabs vary a lot, so their name is built from the title."""
    s = t.lower()
    if k in ("book", "tabs", "flash-cards"):
        if re.search(r"guide to business|business, law|business, and project|business and law|business & law", s):
            base = "Landscape Business & Law Guide" if "landscape" in s else ("Residential Business & Law Guide" if re.search(r"\bresidential\b", s) else "Business & Law Guide")
            if k == "flash-cards": return "Business & Law Flash Cards"
            parts = [base]
            if k == "tabs": parts = [base + " Tabs"]
            else:
                if "highlighted" in s: parts.append("Highlighted & Tabbed")
                elif re.search(r"tabs bundle|\+ tabs|pre-printed tabs", s): parts.append("+ Tabs")
                if "flash card" in s: parts.append("+ Flash Cards")
            ed = ordinal_edition(t)
            return " ".join(parts) + (" (%s)" % ed if ed else "")
        if "home improvement" in s: return "Home Improvement Reference Guide" + (" Tabs" if k == "tabs" else "") + (" (%s)" % ordinal_edition(t) if ordinal_edition(t) else "")
        if k == "tabs": return "Exam Pre-Printed Tabs" + (" + Highlights" if "highlight" in s else "")
        if k == "flash-cards": return "Exam Flash Cards"
        if k == "flash-cards": return "Flash Cards"
        return "Book"
    if k == "book-package" and "complete book set" in s: return "Complete Book Set"
    return KINDS[k][0]

def state_of(t):
    for s in sorted(STATES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(s) + r"\b", t): return s
    return None

def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and").replace("+", "plus")).strip("-")

ALLOW = {"p", "h2", "h3", "h4", "strong", "b", "em", "i", "ul", "ol", "li", "br", "a"}
DROP = {"script", "style", "iframe", "img", "video", "table", "meta"}
class San(HTMLParser):
    def __init__(s): super().__init__(convert_charrefs=True); s.out = []; s.skip = 0
    def handle_starttag(s, t, a):
        if t in DROP: s.skip += 1; return
        if s.skip: return
        if t == "h1": t = "h2"
        if t in ALLOW:
            if t == "b": t = "strong"
            if t == "i": t = "em"
            if t == "a":
                h = dict(a).get("href", "") or ""
                if h.startswith("http"): s.out.append('<a href="%s" rel="noopener" target="_blank">' % h.replace('"', "")); return
                t = "span"
            s.out.append("<%s>" % t)
    def handle_endtag(s, t):
        if t in DROP: s.skip = max(0, s.skip - 1); return
        if s.skip: return
        if t == "h1": t = "h2"
        if t in ALLOW:
            if t == "b": t = "strong"
            if t == "i": t = "em"
            if t == "a": t = "a" if any(x.startswith("<a ") for x in s.out[-40:]) and not s.out[-1] == "</a>" else "span"
            s.out.append("</%s>" % t)
    def handle_startendtag(s, t, a):
        if t == "br" and not s.skip: s.out.append("<br>")
    def handle_data(s, d):
        if not s.skip: s.out.append(d.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def clean_html(h, title):
    p = San(); p.feed(h or ""); out = "".join(p.out)
    out = out.replace("<br></br>", "<br>")
    for _ in range(3): out = re.sub(r"<(p|h2|h3|h4|li|strong|em|span)>\s*</\1>", "", out)
    out = re.sub(r"\s+\n", "\n", out)
    norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower().replace("&amp;", "&"))
    m = re.match(r"^\s*<h[23]>(.*?)</h[23]>", out, re.S)
    if m and norm(re.sub(r"<[^>]+>", "", m.group(1))) == norm(title): out = out[m.end():]
    return out.strip()

def plain(h, n=700):
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()
    import html as _h; t = _h.unescape(t)
    return t if len(t) <= n else t[:n - 3].rsplit(" ", 1)[0] + "..."

def normalize(n):
    """accept a raw GraphQL node or a flattened data record; return one common shape"""
    if "gid" in n:  # flattened record from data/shopify
        vs = [{"id": str(v.get("legacyResourceId") or v["id"].split("/")[-1]), "title": v["title"], "price": v["price"], "compareAt": v.get("compareAtPrice"), "available": True} for v in n["variants"]]
        return {"id": str(n["id"]), "handle": n["handle"], "title": n["title"], "status": n["status"], "type": n.get("productType", ""), "tags": n.get("tags", []),
                "price": n["priceMin"], "maxPrice": n["priceMax"], "image": n.get("image") or "", "images": [n.get("image")] if n.get("image") else [],
                "url": n.get("onlineStoreUrl") or "", "html": n.get("descriptionHtml") or "", "variants": vs}
    vs = [{"id": v["node"]["id"].split("/")[-1], "title": v["node"]["title"], "price": v["node"]["price"], "compareAt": v["node"].get("compareAtPrice"), "available": v["node"].get("availableForSale", True)} for v in n["variants"]["edges"]]
    img = (n.get("featuredImage") or {}).get("url") or ((((n.get("featuredMedia") or {}).get("preview") or {}).get("image") or {}).get("url")) or ""
    imgs = [i["node"]["url"] for i in (n.get("images") or {}).get("edges", [])] or ([img] if img else [])
    return {"id": n["id"].split("/")[-1], "handle": n["handle"], "title": n["title"], "status": n.get("status", "ACTIVE"), "type": n.get("productType", ""), "tags": n.get("tags", []),
            "price": n["priceRangeV2"]["minVariantPrice"]["amount"], "maxPrice": n["priceRangeV2"]["maxVariantPrice"]["amount"], "image": img, "images": imgs,
            "url": n.get("onlineStoreUrl") or "", "html": n.get("descriptionHtml") or "", "variants": vs}

def build(nodes):
    cat, full, skipped = [], {}, []
    for raw in nodes:
        n = normalize(raw)
        if n["status"] != "ACTIVE" or not n["variants"]: continue
        t = n["title"]; ex = exam_of(t)
        if not ex: skipped.append(t); continue
        st = state_of(t); k = kind_of(t, n["type"])
        if not n["variants"]: continue
        cat.append({"id": n["id"], "handle": n["handle"], "title": t, "state": st, "exam": ex, "examName": EXAMS[ex][0], "kind": k, "kindName": kind_name(k, t),
                    "rank": KINDS[k][1], "package": k in PACKAGE_KINDS, "type": n["type"], "price": n["price"], "maxPrice": n["maxPrice"],
                    "compareAt": n["variants"][0]["compareAt"], "image": n["image"], "url": n["url"], "desc": plain(n["html"]), "variants": n["variants"]})
        full[n["id"]] = {"html": clean_html(n["html"], t), "images": n["images"] or [n["image"]]}
    # Shopify has a few listings twice (same thing, same price): keep one of each
    seen, uniq = set(), []
    for p in sorted(cat, key=lambda p: (-len(p["variants"]), int(p["id"]))):
        key = (p["state"], p["exam"], p["kindName"], p["price"])
        if key in seen: skipped.append("duplicate of a listing already kept: " + p["title"]); continue
        seen.add(key); uniq.append(p)
    cat = uniq
    # one URL slug per product, unique within its state + exam
    groups = {}
    for p in sorted(cat, key=lambda p: (p["rank"], float(p["price"]), p["id"])): groups.setdefault((p["state"], p["exam"]), []).append(p)
    for g in groups.values():
        used = set()
        for p in g:
            base = slugify(p["kindName"]); sl = base; i = 2
            while sl in used: sl = "%s-%d" % (base, i); i += 1
            used.add(sl); p["slug"] = sl
    cat.sort(key=lambda p: (p["state"] or "~", EXAMS[p["exam"]][2], p["rank"], float(p["price"])))
    return cat, full, skipped

def main(path):
    nodes = json.load(open(path, encoding="utf-8"))
    cat, full, skipped = build(nodes)
    for t in skipped: print("skipped (no exam matched):", t)
    exams = {k: {"name": v[0], "short": v[1], "order": v[2]} for k, v in EXAMS.items()}
    js = ("/* Auto-generated from the 1 Exam Prep Shopify store (all products with NASCLA in the title), pulled %s. %d products. Regenerate with tools/build_catalog.py rather than hand-editing. */\nwindow.CATALOG=%s;\nwindow.CATALOG_STATES=%s;\nwindow.CATALOG_EXAMS=%s;\n"
          % (datetime.date.today().isoformat(), len(cat), json.dumps(cat, separators=(",", ":")), json.dumps(sorted({p["state"] for p in cat if p["state"]})), json.dumps(exams, separators=(",", ":"))))
    cjs = os.path.join(ROOT, "shared", "catalog.js"); pfull = os.path.join(ROOT, "store", "products-full.json")
    old_js = open(cjs, encoding="utf-8").read() if os.path.exists(cjs) else ""
    old_full = open(pfull, encoding="utf-8").read() if os.path.exists(pfull) else ""
    new_full = json.dumps(full)
    strip = lambda s: re.sub(r"pulled \d{4}-\d{2}-\d{2}", "", s)
    changed = strip(old_js) != strip(js) or old_full != new_full
    if changed:
        os.makedirs(os.path.dirname(cjs), exist_ok=True); os.makedirs(os.path.dirname(pfull), exist_ok=True)
        open(cjs, "w", encoding="utf-8").write(js); open(pfull, "w", encoding="utf-8").write(new_full)
    print("changed" if changed else "unchanged", "(%d products)" % len(cat))
    return changed

if __name__ == "__main__":
    main(sys.argv[1])
