#!/usr/bin/env python3
"""Build the Pass Your NASCLA Exam Prep site.

  python3 build.py

Reads site-config.json, shared/catalog.js, store/products-full.json, content/faq-general.json and
content/posts/*.md, and writes one real HTML page per URL:

  /                                   home
  /<exam>/                            one page per NASCLA exam, listing the states that have it
  /<state>/                           one page per state (and /national/), listing its exams
  /<state>/<exam>/                    the packages for that state and exam
  /<state>/<exam>/<product>/          a product page
  /faq/  and  /faq/<state>/<exam>/    nationwide FAQ, plus state answers taken from the product descriptions
  /blog/ ...                          blog index, posts, tags, RSS feed
  /search/, 404.html, robots.txt, sitemap.xml, llms.txt, agents.md, manifest.webmanifest, icons

Copy and schema text live in this file. Previously generated folders are removed first.
"""
import json, os, re, sys, shutil, html, datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, "site-config.json"), encoding="utf-8"))
SITE = (CFG.get("siteUrl") or "").rstrip("/") + "/" if CFG.get("siteUrl") else None
BRAND = CFG.get("brand", "Pass Your NASCLA Exam Prep")
FUL = CFG.get("fulfillment") or {"name": "1 Exam Prep", "url": "https://1examprep.com", "note": ""}
WM = CFG.get("wordmark") or [BRAND, "", ""]
TODAY = datetime.date.today().isoformat()
LAUNCH = CFG.get("launched", TODAY)
YEAR = TODAY[:4]

cat_js = open(os.path.join(ROOT, "shared", "catalog.js"), encoding="utf-8").read()
def _js(name, nxt):
    a = cat_js.index("window.%s=" % name) + len("window.%s=" % name)
    b = cat_js.index(";\nwindow.%s=" % nxt) if nxt else len(cat_js.rstrip().rstrip(";"))
    return json.loads(cat_js[a:b].rstrip().rstrip(";"))
CATALOG = _js("CATALOG", "CATALOG_STATES")
EXAMS = _js("CATALOG_EXAMS", None)
FULL = json.load(open(os.path.join(ROOT, "store", "products-full.json"), encoding="utf-8"))
GEN_FAQ = json.load(open(os.path.join(ROOT, "content", "faq-general.json"), encoding="utf-8"))["categories"]
sys.path.insert(0, os.path.join(ROOT, "tools")); import blogkit
ALL_POSTS = blogkit.load_posts(os.path.join(ROOT, "content", "posts"), SITE or "")
POSTS = [q for q in ALL_POSTS if q.get("kind", "blog") != "page"]
PAGES = [q for q in ALL_POSTS if q.get("kind", "blog") == "page"]

NATIONAL = "national"
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") if s else NATIONAL
def sname(s): return s or "Nationwide"
EXAM_ORDER = sorted(EXAMS, key=lambda k: EXAMS[k]["order"])
STATES = sorted({p["state"] for p in CATALOG if p["state"]})
NCOMM = ["Alabama", "Arizona", "Arkansas", "Florida", "Georgia", "Louisiana", "Mississippi", "Nevada", "New Mexico", "North Carolina", "Oregon", "South Carolina", "Tennessee", "Utah", "Virginia", "West Virginia"]

# ---------- copy ----------
EXAM_COPY = {
    "commercial-general-building-contractor": {
        "kicker": "115 scored questions · 330 minutes · 70% to pass · open book",
        "intro": "The NASCLA Accredited Examination for Commercial General Building Contractors is one standardized exam that participating states accept in place of their own commercial trade exam. Pass it once and send the same score to every accepting state where you want to bid work.",
        "points": ["Accepted in 16 states and the U.S. Virgin Islands: %s." % ", ".join(NCOMM), "115 scored questions in 330 minutes, open book, with 70% needed to pass.", "Apply through NASCLA at ned.nascla.org; you must be pre-approved before you can schedule.", "Passing replaces the trade exam only. Each state still has its own application and, usually, a business and law exam."]},
    "master-electrical-contractor": {
        "kicker": "NASCLA accredited electrical contractor exam",
        "intro": "NASCLA accredits trade examinations for electrical contractor licenses in participating states. Our master electrical contractor packages are built around the reference books your state's exam allows, with highlighted and tabbed sets, online prep courses and rental options.",
        "points": ["Packages are listed state by state, because each board names its own references and rules.", "Open-book exams reward fast navigation, so the highlighted and tabbed sets are the most popular way to prepare.", "Your state board decides eligibility and licensing; the product pages explain each state's steps."]},
    "journeyman-electrician": {
        "kicker": "NASCLA accredited journeyman exam",
        "intro": "Prep for NASCLA accredited journeyman electrician exams in the states that use them, with the reference books, tabs and online courses matched to each state's exam.",
        "points": ["Choose your state to see the book packages, rentals and online course for that exam.", "Practice finding answers in the references under time pressure; that is what the exam tests.", "Experience, applications and approval to test come from your state board."]},
    "residential-electrical-contractor": {
        "kicker": "NASCLA accredited residential electrical exam",
        "intro": "Prep for NASCLA accredited residential electrical contractor exams, with book packages, highlighted and tabbed sets, rentals and online courses for each participating state.",
        "points": ["Packages are matched to the residential electrical exam in each state that offers it.", "Highlighted and tabbed books cut lookup time on an open-book exam.", "Licensing rules come from each state board; the product pages spell out the steps."]},
    "business-and-law": {
        "kicker": "Contractor's Guide to Business, Law and Project Management",
        "intro": "Most states pair the trade exam with a business and law exam, usually written from NASCLA's Contractor's Guide to Business, Law and Project Management in the edition for your state. We carry each state edition on its own, with pre-printed tabs, or highlighted and tabbed.",
        "points": ["Each state has its own edition of the guide; use the one your state names.", "Tabbed and highlighted copies are cleared for open-book use in most states, but confirm with your candidate bulletin.", "Pair it with your trade exam package from the same state page."]},
}
PRODUCT_FAQ = [("Is the NASCLA exam open book?", "Yes. You bring the approved reference books, so knowing where things are in the books matters as much as knowing the material."),
               ("Are these the actual exam questions?", "No. Real exam questions are confidential. Practice questions are original material written to the same subjects and format, with explanations."),
               ("When will I get it?", "Online courses are delivered by email after purchase. Books ship from our fulfillment center, %s; shipping options are shown at checkout." % FUL["name"]),
               ("Does buying make me eligible to test?", "No. NASCLA approves you to sit the exam and your state board decides on your license. This package gets you ready for the test itself.")]
PLAN = [("1", "Get approved", "Apply at ned.nascla.org and order your books."), ("2", "Tab the books", "Tab and highlight every reference, or start with a pre-tabbed set."),
        ("3", "Core study", "Work through the course and the references chapter by chapter."), ("4", "Lookup drills", "Find answers fast against the clock."),
        ("5", "Full practice", "Sit timed practice exams and review every miss."), ("6", "Final lap", "Weak areas, rest, then exam day.")]

# ---------- small helpers ----------
def esc(s): return html.escape(str(s if s is not None else ""))
def money(v): return "${:,.2f}".format(float(v))
def trim_desc(d, n=158):
    d = re.sub(r"\s+", " ", d or "").strip()
    if len(d) <= n: return d
    cut = d[:n].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + ("" if cut.endswith(".") else ".")
def absurl(path): return (SITE + path) if SITE else "/" + path
def ld(o): return '<script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
def clean(o): return {k: v for k, v in o.items() if v not in (None, "", [])}
def org_ld():
    return clean({"@context": "https://schema.org", "@type": "Organization", "name": BRAND, "legalName": CFG.get("legalName"), "url": SITE or CFG["storeUrl"], "logo": CFG.get("logo"),
                  "telephone": CFG.get("phoneTel"), "email": CFG.get("email"), "sameAs": [v for v in CFG.get("social", {}).values() if v],
                  "parentOrganization": {"@type": "Organization", "name": FUL["name"], "url": FUL["url"]} if FUL["name"] != BRAND else None,
                  "contactPoint": [{"@type": "ContactPoint", "telephone": CFG.get("phoneTel"), "contactType": "sales", "areaServed": "US", "availableLanguage": "English"}]})
def website_ld():
    return {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": SITE or "/",
            "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": absurl("search/?q={search_term_string}")}, "query-input": "required name=search_term_string"}}
def crumbs_ld(items): return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": absurl(p)} for i, (n, p) in enumerate(items)]}
def faq_ld(pairs): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}
def anchor_ids(out):
    seen = set(re.findall(r'\sid="([^"]+)"', out))
    def rep(m):
        tag, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        if re.search(r"\sid=", attrs): return m.group(0)
        base = re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", inner)).lower()).strip("-")[:60] or "section"
        i, hid = 1, base
        while hid in seen: i += 1; hid = "%s-%d" % (base, i)
        seen.add(hid); return '<%s%s id="%s">%s</%s>' % (tag, attrs, hid, inner, tag)
    return re.sub(r"<(h[23])(\s[^>]*)?>(.*?)</\1>", rep, out, flags=re.S)
def rebrand(h): return re.sub(r"(?<![\w/.-])1 ?Exam ?Prep(?![\w.-])", BRAND, h) if FUL["name"] != BRAND else h

ICON_CLOCK = '<svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true"><circle cx="14" cy="14" r="12" fill="none" stroke="#4C8DFF" stroke-width="2.5"/><path d="M14 7v7l5 3" fill="none" stroke="#EEF1F8" stroke-width="2.5" stroke-linecap="round"/></svg>'
ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>'
ICON_SEARCH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">'

PUBLISHER = clean({"@type": "Organization", "name": BRAND, "url": SITE, "logo": {"@type": "ImageObject", "url": CFG.get("logo")}, "telephone": CFG.get("phoneTel"), "email": CFG.get("email"),
                   "parentOrganization": {"@type": "Organization", "name": FUL["name"], "url": FUL["url"]}})
def head(path, title, desc, image, rel, noindex=False, lds=()):
    desc = trim_desc(desc); url = absurl(path) if SITE else None
    md_link = ('<link rel="alternate" type="text/markdown" title="Markdown version for AI assistants" href="%s">' % esc(absurl(path + "index.md"))) if (SITE and not noindex) else ""
    h = ['<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">', "<title>%s</title>" % esc(title), '<meta name="description" content="%s">' % esc(desc),
         '<meta name="robots" content="%s">' % ("noindex, follow" if noindex else "index, follow, max-image-preview:large")]
    if url and not noindex: h.append('<link rel="canonical" href="%s">' % esc(url))
    if md_link: h.append(md_link)
    h += ['<meta property="og:type" content="website">', '<meta property="og:title" content="%s">' % esc(title), '<meta property="og:description" content="%s">' % esc(desc),
          '<meta property="og:site_name" content="%s">' % esc(BRAND), '<meta property="og:locale" content="en_US">']
    if url: h.append('<meta property="og:url" content="%s">' % esc(url))
    img = image or CFG.get("logo")
    if img: h += ['<meta property="og:image" content="%s">' % esc(img), '<meta name="twitter:image" content="%s">' % esc(img)]
    h += ['<meta name="twitter:card" content="summary_large_image">', '<meta name="twitter:title" content="%s">' % esc(title), '<meta name="twitter:description" content="%s">' % esc(desc)]
    if CFG.get("social", {}).get("twitter"): h.append('<meta name="twitter:site" content="@%s">' % CFG["social"]["twitter"].rstrip("/").split("/")[-1])
    h += ['<meta name="theme-color" content="#0B0F1A">', '<link rel="icon" href="%sshared/favicon.png" type="image/png" sizes="64x64">' % rel, '<link rel="icon" href="%sshared/favicon.svg" type="image/svg+xml">' % rel,
          '<link rel="apple-touch-icon" href="%sshared/apple-touch-icon.png">' % rel, '<link rel="manifest" href="%smanifest.webmanifest">' % rel,
          '<link rel="alternate" type="application/rss+xml" title="%s blog" href="%sblog/feed.xml">' % (esc(BRAND), rel), FONTS, '<link rel="stylesheet" href="%sshared/site.css">' % rel]
    if CFG.get("googleSiteVerification"): h.append('<meta name="google-site-verification" content="%s">' % esc(CFG["googleSiteVerification"]))
    if CFG.get("gtagId"): h.append('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","%s");</script>' % (CFG["gtagId"], CFG["gtagId"]))
    if CFG.get("gtmId"): h.append("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s);j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','%s');</script>" % CFG["gtmId"])
    if CFG.get("metaPixelId"): h.append("<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','%s');fbq('track','PageView');</script>" % CFG["metaPixelId"])
    h.append('<script>window.SITE=%s;</script>' % json.dumps({"brand": BRAND, "storeUrl": CFG["storeUrl"], "fulfillment": FUL["name"]}))
    for o in lds: h.append(ld(o))
    if url and not noindex:
        h.append(ld({"@context": "https://schema.org", "@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc, "inLanguage": "en-US", "datePublished": LAUNCH, "dateModified": TODAY,
                     "isPartOf": {"@type": "WebSite", "url": SITE, "name": BRAND}, "publisher": PUBLISHER, "about": {"@type": "Thing", "name": "NASCLA contractor licensing exams"},
                     "encoding": {"@type": "MediaObject", "encodingFormat": "text/markdown", "contentUrl": absurl(path + "index.md")}}))
    return "\n".join(h)

def dash_tag():
    """dashboard tracker, placed in <body> as the dashboard's Settings > Tracker snippet shows"""
    if not (CFG.get("dashboardUrl") and CFG.get("siteKey")): return ""
    return '<script>window.__dashCustom=true;</script><script src="%s/t.js" data-site="%s" defer></script>' % (esc(CFG["dashboardUrl"].rstrip("/")), esc(CFG["siteKey"]))
def wordmark(): return '%s<span class="wm">%s<span>%s</span>%s</span>' % (ICON_CLOCK, esc(WM[0]), esc(WM[1]), esc(WM[2])) if len(WM) == 3 else ICON_CLOCK + esc(BRAND)
def header(rel, cta_href, cta_label="Find my exam", current=""):
    home = rel or "./"
    links = [("Exams", home + "#exams", "exams"), ("States", home + "#states", "states"), ("FAQ", rel + "faq/", "faq"), ("Blog", rel + "blog/", "blog")]
    return ('<a class="skip" href="#main">Skip to content</a><header class="nav"><div class="wrap"><a class="brand" href="%s" aria-label="%s home">%s</a>'
            '<nav class="nav-links" aria-label="Main">%s</nav><div class="nav-tools"><a class="nav-phone" href="tel:%s" aria-label="Call %s">%s<span>%s</span></a>'
            '<button type="button" class="nav-search" data-sopen aria-label="Search the site">%s</button><a class="btn btn-buy btn-sm" href="%s">%s</a></div></div></header>'
            % (home, esc(BRAND), wordmark(), "".join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if k == current else "", n) for n, h, k in links),
               CFG["phoneTel"], esc(CFG["phone"]), ICON_PHONE, esc(CFG["phone"]), ICON_SEARCH, cta_href, esc(cta_label)))
def footer(rel):
    home = rel or "./"
    soc = "".join('<li><a href="%s" rel="noopener" target="_blank">%s</a></li>' % (esc(u), k.capitalize()) for k, u in CFG.get("social", {}).items() if u)
    exams = "".join('<li><a href="%s%s/">%s</a></li>' % (rel, k, esc(EXAMS[k]["name"])) for k in EXAM_ORDER)
    pop = "".join('<li><a href="%s%s/">%s</a></li>' % (rel, slug(s), s) for s in ["Florida", "Georgia", "North Carolina", "Tennessee", "Alabama", "Arizona"] if s in STATES)
    return ('<footer class="site-footer"><div class="wrap"><div class="cols"><div><a class="brand" href="%s">%s</a><p style="margin-top:12px">%s</p><p class="contact"><a href="tel:%s">%s</a><a href="mailto:%s">%s</a></p></div>'
            '<nav aria-label="Exams"><h2>Exams</h2><ul>%s</ul></nav><nav aria-label="Popular states"><h2>Popular states</h2><ul>%s<li><a href="%s#states">All states</a></li></ul></nav>'
            '<nav aria-label="Help"><h2>Help</h2><ul><li><a href="%sfaq/">FAQ</a></li><li><a href="%sblog/">Blog</a></li><li><a href="%ssearch/">Search</a></li></ul><h2 style="margin-top:20px">Follow</h2><ul>%s</ul></nav></div>'
            '<p class="fine"><strong>%s</strong> &copy; <span data-year>%s</span>. %s Prices come from the fulfillment store and were last checked <time datetime="%s">%s</time>; the price at checkout is the one that applies. '
            'Not affiliated with NASCLA, any state licensing board or testing vendor. Purchasing does not grant exam eligibility or a license.</p></div></footer>'
            % (home, wordmark(), esc(CFG.get("tagline", "")), CFG["phoneTel"], esc(CFG["phone"]), CFG["email"], CFG["email"], exams, pop, home, rel, rel, rel, soc,
               esc(BRAND), YEAR, esc(FUL.get("note") or ""), TODAY, datetime.date.fromisoformat(TODAY).strftime("%B %-d, %Y")))

from html.parser import HTMLParser
class MD(HTMLParser):
    """turns a page's main HTML into plain Markdown for AI assistants"""
    SKIP = {"script", "style", "svg", "button", "form", "img", "input", "label", "noscript"}
    SKIPCLS = ("stickybar", "skip", "srch", "thumbs", "pc-badge")
    def __init__(s, base):
        super().__init__(convert_charrefs=True); s.base = base; s.out = []; s.skip = 0; s.stack = []; s.href = None; s.lists = []
    def sp(s):
        if s.out and not s.out[-1].endswith((" ", "\n")): s.out.append(" ")
    def nl(s, n=2):
        s.out.append("\n" * n)
    def handle_starttag(s, tag, attrs):
        a = dict(attrs); cls = a.get("class") or ""
        skip = tag in s.SKIP or any(c in cls.split() for c in s.SKIPCLS) or a.get("aria-hidden") == "true"
        if tag in ("br", "hr", "img", "input", "meta", "link"):
            if tag == "br" and not s.skip: s.out.append("  \n")
            return
        s.stack.append(skip)
        if skip: s.skip += 1; return
        if s.skip: return
        if tag in ("h1", "h2", "h3", "h4"): s.nl(); s.out.append("#" * int(tag[1]) + " ")
        elif tag == "summary": s.nl(); s.out.append("### ")
        elif tag in ("p", "details", "section", "article", "aside", "div", "dl", "dt", "dd") and not s.lists: s.nl(1)
        elif tag in ("ul", "ol"): s.lists.append([tag, 0]); s.nl(1)
        elif tag == "li":
            s.out.append("\n" + "  " * (len(s.lists) - 1))
            if s.lists and s.lists[-1][0] == "ol": s.lists[-1][1] += 1; s.out.append("%d. " % s.lists[-1][1])
            else: s.out.append("- ")
        elif tag in ("strong", "b"): s.out.append("**")
        elif tag in ("em", "i"): s.out.append("*")
        elif tag == "s": s.sp(); s.out.append("(was ")
        elif tag in ("span", "small", "time") and s.out and not s.out[-1].endswith((" ", "\n", "[", "(")): s.out.append(" ")
        elif tag == "a":
            if s.out and s.out[-1].endswith(")"): s.out.append(" \u00b7 ")
            h = a.get("href") or ""
            if h and not h.startswith(("#", "javascript")):
                from urllib.parse import urljoin
                s.href = h if h.startswith(("http", "mailto", "tel")) else urljoin(s.base, h)
                s.out.append("[")
    def handle_endtag(s, tag):
        if tag in ("br", "hr", "img", "input", "meta", "link"): return
        skip = s.stack.pop() if s.stack else False
        if skip: s.skip -= 1; return
        if s.skip: return
        if tag in ("h1", "h2", "h3", "h4", "summary", "p", "dt", "dd"): s.nl(1)
        elif tag in ("ul", "ol"):
            if s.lists: s.lists.pop()
            s.nl(1)
        elif tag in ("strong", "b"): s.out.append("**")
        elif tag in ("em", "i"): s.out.append("*")
        elif tag == "a" and s.href: s.out.append("](%s)" % s.href); s.href = None
        elif tag == "s": s.out.append(")")
    def handle_data(s, d):
        if s.skip: return
        d = re.sub(r"\s+", " ", d)
        if d.strip() or (s.out and not s.out[-1].endswith(("\n", " "))): s.out.append(d)
    def text(s):
        md = "".join(s.out)
        md = re.sub(r"\*\*\s*\*\*", "", md); md = re.sub(r"\[\s*\]\([^)]*\)", "", md)
        md = re.sub(r"[ \t]+\n", "\n", md); md = re.sub(r"\n{3,}", "\n\n", md)
        return md.strip() + "\n"
def write_md(parts, path, title, desc, body):
    if not SITE: return
    p = MD(absurl(path)); p.feed(body)
    body_md = p.text()
    if not re.search(r"^# ", body_md, re.M): body_md = "# %s\n\n%s" % (title, body_md)
    md = ("---\ntitle: %s\nurl: %s\nupdated: %s\nsite: %s\ndescription: %s\n---\n\n" % (title, absurl(path), TODAY, BRAND, trim_desc(desc, 300).replace("\n", " "))) + body_md
    md += "\n---\n\nSource: %s  \nPublisher: %s. Orders are fulfilled by %s (%s). Phone %s, email %s.  \nPrices change; the product page and checkout show the current price.\n" % (absurl(path), BRAND, FUL["name"], FUL["url"], CFG["phone"], CFG["email"])
    d = os.path.join(ROOT, *parts) if parts else ROOT
    open(os.path.join(d, "index.md"), "w", encoding="utf-8").write(md)

GENERATED, URLS = [], []
def write(parts, body, title, desc, image=None, lds=(), noindex=False, cta=("#", "Find my exam"), current="", route=None, scripts="", sitemap=True, priority="0.6"):
    rel = "../" * len(parts); path = "/".join(parts) + ("/" if parts else "")
    cta_href = cta[0] if cta[0].startswith(("http", "#")) else rel + cta[0]
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n%s\n</head>\n<body>\n%s\n<main id=\"main\">\n%s\n</main>\n%s\n<script>window.ROUTE=%s;</script>%s<script src=\"%sshared/site.js\" defer></script><script src=\"%sshared/track.js\" defer></script>%s\n</body>\n</html>\n"
            % (head(path, title, desc, image, rel, noindex, lds), header(rel, cta_href, cta[1], current), body, footer(rel), json.dumps(dict(route or {}, depth=len(parts))), scripts, rel, rel, dash_tag()))
    page = page.replace("{{REL}}", rel).replace("{{HOME}}", rel or "./")
    d = os.path.join(ROOT, *parts) if parts else ROOT; os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(anchor_ids(page))
    if not noindex: write_md(parts, path, title, desc, body)
    if parts: GENERATED.append(path.rstrip("/"))
    if SITE and sitemap and not noindex: URLS.append((absurl(path), priority))

def crumbs_html(items, rel):
    out = []
    for i, (n, p) in enumerate(items):
        out.append(('<a href="%s">%s</a>' % ((rel + p) if p else (rel or "./"), esc(n))) if i < len(items) - 1 else '<span aria-current="page">%s</span>' % esc(n))
    return ('<nav class="crumbs" aria-label="Breadcrumb">%s</nav><p class="upd">Updated <time datetime="%s">%s</time> \u00b7 prices checked against the %s store</p>'
            % ('<span aria-hidden="true">/</span>'.join(out), TODAY, datetime.date.fromisoformat(TODAY).strftime("%B %-d, %Y"), esc(FUL["name"])))
def takeaways(items):
    items = [i for i in items if i][:4]
    return ('<aside class="takeaways" aria-labelledby="key-takeaways"><h2 id="key-takeaways">Key takeaways</h2><ul>%s</ul></aside>' % "".join("<li>%s</li>" % esc(i) for i in items)) if items else ""
def faq_html(pairs, open_first=True):
    return '<div class="faq">%s</div>' % "".join('<details%s><summary>%s</summary><p>%s</p></details>' % (" open" if open_first and i == 0 else "", esc(q), esc(a)) for i, (q, a) in enumerate(pairs))
def quick_answers(pairs):
    """answer-first block: the questions people ask AI assistants, answered in one or two sentences"""
    return '<section class="qa" aria-labelledby="quick-answers"><h2 id="quick-answers">Quick answers</h2>%s</section>' % "".join('<div class="qa-item"><h3>%s</h3><p>%s</p></div>' % (esc(q), esc(a)) for q, a in pairs)
def final_cta(kicker, title, text, href, label):
    return '<section class="sec-tight"><div class="wrap"><div class="final"><div><span class="eyebrow">%s</span><h2>%s</h2><p>%s</p></div><a class="btn btn-buy" href="%s">%s</a></div></div></section>' % (esc(kicker), esc(title), esc(text), href, esc(label))

# ---------- catalog views ----------
def ppath(p): return "%s/%s/%s/" % (slug(p["state"]), p["exam"], p["slug"])
def items_for(state, exam): return [p for p in CATALOG if p["state"] == state and p["exam"] == exam]
def buy_url(vid): return "https://1examprep.com/cart/%s:1" % vid
def save_html(c, n): return ('<s class="pc-was">%s</s><span class="pc-save">Save %d%%</span>' % (money(c), round((c - n) / c * 100))) if c and c > n else ""
def short_desc(p, n=24):
    d = rebrand(p["desc"])
    d = re.sub(re.escape(p["title"]), "", d, flags=re.I).replace("\u2122", "")
    w = d.strip(" .:-").split()
    return " ".join(w[:n]) + ("…" if len(w) > n else "")
FEATURED = "ultimate"
def card(p, rel):
    c, n = float(p.get("compareAt") or 0), float(p["price"]); feat = p["kind"] == FEATURED
    frm = '<span class="pc-from">options to %s</span>' % money(p["maxPrice"]) if p.get("maxPrice") and float(p["maxPrice"]) > n else ""
    return ('<article class="pc%s" data-id="%s">%s<div class="pc-img"><img src="%s" alt="%s" loading="lazy" width="400" height="300"></div><div class="pc-body"><span class="pc-kind">%s</span>'
            '<h3 class="pc-name"><a href="%s%s">%s</a></h3><p class="pc-desc">%s</p><div class="pc-price"><span class="pc-now">%s</span>%s%s</div>'
            '<div class="pc-actions"><a class="btn btn-buy" href="%s" rel="noopener">Buy now</a><a class="btn btn-ghost" href="%s%s" data-details="%s">Details</a></div></div></article>'
            % (" pc--featured" if feat else "", p["id"], '<span class="pc-badge">Books + course</span>' if feat else "", esc(p["image"]), esc(p["title"]), esc("%s · %s" % (sname(p["state"]), EXAMS[p["exam"]]["short"])),
               rel, ppath(p), esc(p["kindName"]), esc(short_desc(p)), money(n), save_html(c, n), frm, buy_url(p["variants"][0]["id"]), rel, ppath(p), p["id"]))
def row(p, rel):
    return ('<div class="row" data-id="%s"><img src="%s" alt="" loading="lazy" width="64" height="64"><div class="t"><a href="%s%s">%s</a><small>%s</small></div><span class="p">%s</span><a class="btn btn-buy btn-sm" href="%s" rel="noopener">Buy now</a></div>'
            % (p["id"], esc(p["image"]), rel, ppath(p), esc(p["kindName"]), esc(sname(p["state"]) + " · " + EXAMS[p["exam"]]["short"]), money(p["price"]), buy_url(p["variants"][0]["id"])))
def price_range(ps):
    v = [float(p["price"]) for p in ps]
    return (min(v), max(v)) if v else (0, 0)

# ---------- FAQ answers taken from the product descriptions ----------
PRODUCT_Q = re.compile(r"\b(this|the)\s+([\w+&\- ]*?)(combo|package|product|kit|bundle|set|course|guide|rental|training|book|tabs)\b|\bincluded\b|\binclude\b|\bships?\b|\bshipping\b|\bdelivered\b|\brefund|\bprice|\bcost\b|\bdiscount|\brent\b|\breturn", re.I)
STOP = set("the a an is are do does i my for of in on to and or what which who how can be with this that it its exam exams nascla licensing license test".split())
def split_desc(hx):
    """return (body_html, [(q, a)]) separating the FAQ block at the end of a description"""
    m = re.search(r"<h[23]>\s*(?:<strong>)?\s*(FAQ[^<]*|Frequently Asked Questions[^<]*)(?:</strong>)?\s*</h[23]>", hx or "", re.I)
    if not m: return hx or "", []
    pairs = []
    for qm in re.finditer(r"<h[23]>(.*?)</h[23]>\s*((?:(?!<h[23]>).)*)", hx[m.end():], re.S):
        q = html.unescape(re.sub(r"<[^>]+>", "", qm.group(1))).strip(); q = re.sub(r"^\s*(faq|q)\s*[:.]\s*", "", q, flags=re.I)
        a = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", qm.group(2)))).strip()
        if q and a: pairs.append((q, a))
    return hx[:m.start()], pairs
def qkey(q):
    q = re.sub(r"[^a-z0-9 ]", " ", q.lower())
    return frozenset(w for w in q.split() if w not in STOP and len(w) > 2)
def state_faqs():
    groups = {}
    for p in sorted(CATALOG, key=lambda p: -p["rank"]):
        _, pairs = split_desc(FULL.get(p["id"], {}).get("html", ""))
        g = groups.setdefault((p["state"], p["exam"]), [])
        for q, a in pairs:
            if PRODUCT_Q.search(q): continue
            a = rebrand(a); k = qkey(q)
            if not k: continue
            dup = next((it for it in g if len(k & it["k"]) / (len(k | it["k"]) or 1) >= 0.7), None)
            if dup:
                if len(a) > len(dup["a"]): dup["q"], dup["a"] = q, a
            else: g.append({"q": q, "a": a, "k": k})
    return {k: [(i["q"], i["a"]) for i in v] for k, v in groups.items() if v}
STATE_FAQS = state_faqs()

# ---------- remove previously generated folders ----------
manifest = os.path.join(ROOT, "generated-pages.txt")
KEEP = {"shared", "store", "content", "tools", "data", "brand", ".github", ".git"}
if os.path.exists(manifest):
    for line in open(manifest):
        top = line.strip().split("/")[0]
        if top and top not in KEEP and os.path.isdir(os.path.join(ROOT, top)): shutil.rmtree(os.path.join(ROOT, top))

# ---------- home ----------
def home():
    rel = ""
    exam_cards = ""
    for k in EXAM_ORDER:
        ps = [p for p in CATALOG if p["exam"] == k]; sts = sorted({p["state"] for p in ps if p["state"]})
        exam_cards += ('<a class="exam" href="%s/"><span class="k">%s</span><h3>%s</h3><p>%s</p><span class="more">%d state%s · %d products →</span></a>'
                       % (k, esc(EXAM_COPY[k]["kicker"].upper() if k != "commercial-general-building-contractor" else "ACCEPTED IN 16 STATES + USVI"), esc(EXAMS[k]["name"]), esc(trim_desc(EXAM_COPY[k]["intro"], 120)), len(sts), "" if len(sts) == 1 else "s", len(ps)))
    st_items = ""
    for s in STATES + [None]:
        ex = [k for k in EXAM_ORDER if items_for(s, k)]
        st_items += '<li><a href="%s/">%s</a><span>%s</span></li>' % (slug(s), esc(sname(s)), "".join('<a href="%s/%s/">%s</a>' % (slug(s), k, esc(EXAMS[k]["short"])) for k in ex))
    natl = sorted([p for p in CATALOG if not p["state"] and p["exam"] == "commercial-general-building-contractor" and p["package"]], key=lambda p: (p["rank"], float(p["price"])))
    gen_pairs = [(q, a) for c in GEN_FAQ for q, a in c["items"]]
    home_faq = [gen_pairs[i] for i in (2, 5, 6, 8, 9, 15) if i < len(gen_pairs)]
    lo, hi = price_range(CATALOG)
    body = ('<section class="hero"><div class="wrap"><div class="hero-copy"><span class="eyebrow">NASCLA exam prep, state by state</span>'
            '<h1>Walk in ready.<br>Walk out licensed in <em>16 states</em>.</h1>'
            '<p class="lead">Prep for the NASCLA Accredited Examination for Commercial General Building Contractors, plus NASCLA electrical and business and law exams. Book packages, highlighted and tabbed sets, rentals and online courses for %d states.</p>'
            '<div class="hero-ctas"><a class="btn btn-buy" href="#exams">Find my exam</a><a class="btn btn-ghost" href="#plan">See the study plan</a></div>%s</div>'
            '<div class="clock" aria-label="NASCLA commercial exam at a glance"><div class="clock-top"><span>Commercial exam clock</span><span class="pill">Open book</span></div>'
            '<div class="clock-time" aria-hidden="true">5:30:00</div><div class="clock-bar" aria-hidden="true"><i></i></div>'
            '<div class="stats"><div><b>115</b><small>scored questions</small></div><div><b>~2.9</b><small>min each</small></div><div><b>70%%</b><small>to pass</small></div></div></div></div></section>'
            % (len(STATES), takeaways(["%d NASCLA prep products across %d states and nationwide editions, from %s to %s." % (len(CATALOG), len(STATES), money(lo), money(hi)),
                                      "The commercial exam is 115 scored questions in 330 minutes, open book, 70%% to pass, and accepted in 16 states plus the U.S. Virgin Islands.",
                                      "Every Buy now button opens secure checkout at our fulfillment center, %s." % FUL["name"]]).replace("%%", "%")))
    body += '<section class="sec" id="exams"><div class="wrap"><span class="eyebrow">Pick your exam</span><h2>Which NASCLA exam are you taking?</h2><p class="lead-s">Choose the exam, then your state. Every state page lists the books, tabs, rentals and online courses for that exam.</p><div class="exams">%s</div></div></section>' % exam_cards
    body += '<section class="sec sec-alt" id="plan"><div class="wrap"><span class="eyebrow">How to pass</span><h2>Your study plan</h2><p class="lead-s">A sample six-week path for an open-book NASCLA exam. Go faster or slower to fit your schedule.</p><div class="plan">%s</div></div></section>' % "".join('<div><b>WEEK %s</b><h3>%s</h3><p>%s</p></div>' % (n, esc(t), esc(d)) for n, t, d in PLAN)
    if natl:
        body += '<section class="sec"><div class="wrap"><span class="eyebrow">Nationwide editions</span><h2>Commercial General Building Contractor packages</h2><p class="lead-s">The NASCLA commercial exam is the same in every accepting state. These nationwide packages work wherever you test; state editions add the business and law material for your state.</p><div class="grid" id="rail">%s</div></div></section>' % "".join(card(p, rel) for p in natl[:6])
    body += '<section class="sec sec-alt" id="states"><div class="wrap"><span class="eyebrow">By state</span><h2>Every state we carry</h2><p class="lead-s">Pick your state to see its exams. Each board sets its own rules for using NASCLA scores, and the product pages explain the steps.</p><ul class="states">%s</ul></div></section>' % st_items
    body += '<section class="sec"><div class="wrap" style="max-width:860px"><h2>Questions</h2>%s<p style="margin-top:20px"><a href="faq/">All %d questions</a></p></div></section>' % (faq_html(home_faq), len(gen_pairs) + sum(len(v) for v in STATE_FAQS.values()))
    body += final_cta("Ready when you are", "Pick your exam and state, then choose how much help you want.", "From a single tabbed guide to The 1 Package with licensing and business setup.", "#exams", "Find my exam")
    write([], body, "NASCLA Exam Prep: Commercial, Electrical, Business & Law", "NASCLA exam prep for the commercial general building contractor exam accepted in 16 states, plus NASCLA electrical and business and law exams. Books, tabbed sets, rentals and online courses by state.",
          CFG.get("logo"), [org_ld(), website_ld(), faq_ld(home_faq), crumbs_ld([("Home", "")])], cta=("#exams", "Find my exam"), priority="1.0")
home()

# ---------- exam hubs: /<exam>/ ----------
for k in EXAM_ORDER:
    ps = [p for p in CATALOG if p["exam"] == k]; sts = sorted({p["state"] for p in ps if p["state"]}); natl = sorted([p for p in ps if not p["state"]], key=lambda p: (p["rank"] == 0, p["rank"], float(p["price"])))
    rel = "../"; E = EXAMS[k]; C = EXAM_COPY[k]; lo, hi = price_range(ps)
    items = "".join('<li><a href="%s%s/%s/">%s</a><span><a href="%s%s/%s/">%d products from %s</a></span></li>' % (rel, slug(s), k, esc(s), rel, slug(s), k, len(items_for(s, k)), money(price_range(items_for(s, k))[0])) for s in sts)
    body = ('<section class="phead"><div class="wrap">%s<span class="eyebrow">%s</span><h1>NASCLA %s Exam Prep</h1><p class="lead">%s</p>%s</div></section>'
            % (crumbs_html([("Home", ""), (E["name"], k + "/")], rel), esc(C["kicker"]), esc(E["name"]), esc(C["intro"]), takeaways(["%d products for this exam across %d state%s%s, from %s to %s." % (len(ps), len(sts), "" if len(sts) == 1 else "s", " plus nationwide editions" if natl else "", money(lo), money(hi))] + C["points"][:3])))
    if k == "commercial-general-building-contractor":
        qa = [("Which states accept the NASCLA commercial exam?", "%s and the U.S. Virgin Islands accept the NASCLA Accredited Examination for Commercial General Building Contractors. Each board sets its own rules for using the score." % ", ".join(NCOMM)),
              ("What is on the NASCLA commercial exam?", "115 scored questions in 330 minutes, open book, with 70 percent needed to pass. It covers commercial building regulations, best practices and terminology, answered from the approved reference books."),
              ("How should I prepare for the NASCLA commercial exam?", "Get the approved reference books, tab and highlight them, work an online course or study guide, then sit timed practice exams. Prep here runs from %s to %s, from a single online course to The 1 Package with licensing and business setup." % (money(lo), money(hi)))]
    else:
        qa = [("Where can I get %s exam prep?" % E["name"].lower(), "We carry %s prep for %s%s." % (E["name"].lower(), ", ".join(sts), " plus nationwide editions" if natl else "")),
              ("What does %s prep cost?" % E["name"].lower(), "From %s to %s, depending on whether you want a single book or tabs, a book package, a rental, an online course or an all-inclusive package." % (money(lo), money(hi)))]
    body += '<section class="sec-tight" style="padding-top:0"><div class="wrap">%s</div></section>' % quick_answers(qa)
    body += '<section class="sec-tight"><div class="wrap"><h2 style="font-size:28px">Choose your state</h2><ul class="states">%s</ul></div></section>' % items
    if natl:
        pk = [p for p in natl if p["package"]]; ad = [p for p in natl if not p["package"]]
        body += '<section class="sec-tight"><div class="wrap"><div class="group-h"><h2>Nationwide editions</h2><p>Not tied to one state.</p></div>%s%s</div></section>' % (('<div class="grid" id="rail">%s</div>' % "".join(card(p, rel) for p in pk)) if pk else "", ('<div class="rows" style="margin-top:18px">%s</div>' % "".join(row(p, rel) for p in ad)) if ad else "")
    body += '<section class="sec-tight"><div class="wrap" style="max-width:860px"><h2 style="font-size:28px">About this exam</h2><ul class="prose">%s</ul></div></section>' % "".join("<li>%s</li>" % esc(x) for x in C["points"])
    title = "NASCLA %s Exam Prep" % E["name"]
    write([k], body, title if len(title) <= 60 else "NASCLA %s Exam Prep" % E["short"], "%s %d products across %d states, from %s." % (trim_desc(C["intro"], 110), len(ps), len(sts), money(lo)),
          (ps[0]["image"] if ps else None), [crumbs_ld([("Home", ""), (E["name"], k + "/")]), faq_ld(qa), {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": absurl(k + "/"),
          "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": absurl("%s/%s/" % (slug(s), k)), "name": "%s %s" % (s, E["name"])} for i, s in enumerate(sts)]}}],
          cta=("#main", "Choose my state"), route={"exam": k}, priority="0.9")

# ---------- long-form state guides (content/states/<slug>.json) ----------
GUIDE_DIR = os.path.join(ROOT, "content", "states")
def load_guide(sl):
    if os.environ.get("NO_GUIDES"): return None  # NO_GUIDES=1 python3 build.py builds the plain state pages
    f = os.path.join(GUIDE_DIR, sl + ".json")
    if not os.path.exists(f): return None
    try: G = json.load(open(f, encoding="utf-8"))
    except Exception as e: print("guide skipped (bad JSON):", f, e); return None
    # a guide goes live only once it has been fact-checked and marked "status": "published";
    # GUIDES_PREVIEW=1 python3 build.py renders drafts too, for checking locally
    if G.get("status") != "published" and not os.environ.get("GUIDES_PREVIEW"): return None
    return G
def md_inline(text, rel):
    """plain text with [label](url) links -> safe HTML; links to this site become relative"""
    out, pos = [], 0
    for m in re.finditer(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", text):
        out.append(esc(text[pos:m.start()])); url = m.group(2)
        if SITE and url.startswith(SITE): out.append('<a href="%s%s">%s</a>' % (rel, esc(url[len(SITE):]), esc(m.group(1))))
        else: out.append('<a href="%s" rel="noopener" target="_blank">%s</a>' % (esc(url), esc(m.group(1))))
        pos = m.end()
    out.append(esc(text[pos:])); return "".join(out)
def plain_md(text): return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
def guide_words(G):
    parts = list(G.get("intro", [])) + [x for s_ in G.get("sections", []) for x in [s_.get("h2", "")] + s_.get("paragraphs", []) + s_.get("list", [])] + [x for q, a in G.get("faq", []) for x in (q, a)]
    return len(" ".join(plain_md(p) for p in parts).split())
def sec_id(h): return re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-")[:60] or "section"
def guide_page(s, G, ex, ps, rel, qa):
    nm = s; words = guide_words(G); mins = max(1, round(words / 230))
    intro = G.get("intro", [])
    lead = ('<p class="lead">%s</p>' % md_inline(intro[0], rel)) if intro else ""
    more_intro = "".join('<p class="lead-2">%s</p>' % md_inline(p, rel) for p in intro[1:])
    byline = '<p class="byline">By %s \u00b7 %d min read \u00b7 %d official sources cited</p>' % (esc(BRAND), mins, len(G.get("sources", [])))
    tk = takeaways(["%d %s products for %d exam%s, from %s to %s." % (len(ps), s, len(ex), "" if len(ex) == 1 else "s", money(price_range(ps)[0]), money(price_range(ps)[1])),
                    ("%s accepts the NASCLA commercial building exam in place of its state trade exam; the board's other requirements still apply." % s) if s in NCOMM else "",
                    "Books ship from our fulfillment center, %s; online courses arrive by email." % FUL["name"]])
    cards = "".join('<a class="exam" href="%s/"><span class="k">%d PRODUCTS \u00b7 FROM %s</span><h3>%s %s</h3><p>%s</p><span class="more">See %s packages \u2192</span></a>'
                    % (k, len(items_for(s, k)), money(price_range(items_for(s, k))[0]), esc(s), esc(EXAMS[k]["name"]), esc(trim_desc(EXAM_COPY[k]["intro"], 110)), esc(EXAMS[k]["short"])) for k in ex)
    secs, toc = [], []
    for s_ in G.get("sections", []):
        h = s_.get("h2", "").strip()
        if not h: continue
        sid = sec_id(h); toc.append('<li><a href="#%s">%s</a></li>' % (sid, esc(h)))
        html_ = "".join("<p>%s</p>" % md_inline(p, rel) for p in s_.get("paragraphs", []))
        if s_.get("list"):
            tag = "ol" if s_.get("ordered") else "ul"
            html_ += "<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % md_inline(x, rel) for x in s_["list"]), tag)
        secs.append('<section aria-labelledby="%s"><h2 id="%s">%s</h2>%s</section>' % (sid, sid, esc(h), html_))
    faq_pairs = [(plain_md(q), plain_md(a)) for q, a in G.get("faq", [])]
    faq_block = ('<section class="faq-sec" aria-labelledby="faq-h"><h2 id="faq-h">%s</h2>%s</section>' % (esc("%s NASCLA exam and license FAQ" % s), faq_html(faq_pairs))) if faq_pairs else ""
    srcs = G.get("sources", [])
    src_block = ('<section class="sources" aria-labelledby="src-h"><h2 id="src-h">Sources</h2><p>Facts on this page come from these official sources, checked %s. Rules and fees change, so confirm with the board before you apply.</p><ol>%s</ol></section>'
                 % (datetime.date.fromisoformat(TODAY).strftime("%B %-d, %Y"), "".join('<li><a href="%s" rel="noopener" target="_blank">%s</a></li>' % (esc(x["url"]), esc(x["title"])) for x in srcs))) if srcs else ""
    pk_rows = ""
    for k in ex:
        pk = sorted([p for p in items_for(s, k) if p["package"]], key=lambda p: (p["rank"], float(p["price"])))
        if not pk: pk = sorted(items_for(s, k), key=lambda p: float(p["price"]))[:4]
        pk_rows += ('<div class="group-h"><h3 style="font-size:22px;margin:0">%s %s packages</h3><p><a href="%s/">All %d products \u2192</a></p></div><div class="grid">%s</div>'
                    % (esc(s), esc(EXAMS[k]["name"]), k, len(items_for(s, k)), "".join(card(p, rel) for p in pk[:3])))
    side_pk = "".join('<li><a href="%s/">%s</a> <small>from %s</small></li>' % (k, esc(EXAMS[k]["name"]), money(price_range(items_for(s, k))[0])) for k in ex)
    near = [x for x in STATES if x != s][:0]
    body = ('<section class="phead"><div class="wrap" style="max-width:980px">%s<h1>%s</h1>%s%s%s</div></section>'
            % (crumbs_html([("Home", ""), (nm, slug(s) + "/")], rel), esc(G.get("h1") or "%s NASCLA Exam Prep" % s), byline, lead, more_intro))
    body += '<section class="sec-tight" style="padding-top:0"><div class="wrap">%s%s</div></section>' % (quick_answers(qa), tk)
    body += '<section class="sec-tight"><div class="wrap"><h2 style="font-size:28px">Choose your %s exam</h2><div class="exams">%s</div></div></section>' % (esc(s), cards)
    body += ('<section class="sec-tight"><div class="wrap"><div class="layout"><div class="main-col"><article class="prose guide">%s</article>%s%s</div>'
             '<aside class="side-col"><div class="side-card toc"><h3>On this page</h3><ol>%s</ol></div><div class="side-card"><h3>%s exam prep</h3><ul>%s</ul></div></aside></div></div></section>'
             % ("".join(secs), faq_block, src_block, "".join(toc), esc(s), side_pk))
    body += '<section class="sec sec-alt" id="packages"><div class="wrap"><span class="eyebrow">Shop %s</span><h2>%s NASCLA exam prep packages</h2><p class="lead-s">Every package is built for the open-book format. Buy now opens secure checkout at %s.</p>%s</div></section>' % (esc(s), esc(s), esc(FUL["name"]), pk_rows)
    body += final_cta("%s licensing" % s, "Ready to study for your %s exam?" % s, "Pick your exam above, or call %s and we will help you choose." % CFG["phone"], "#packages", "See %s packages" % s)
    art = clean({"@context": "https://schema.org", "@type": "Article", "headline": (G.get("h1") or G.get("title"))[:110], "description": G.get("meta_description"), "url": absurl(slug(s) + "/"),
                 "datePublished": LAUNCH, "dateModified": TODAY, "inLanguage": "en-US", "wordCount": words, "keywords": ", ".join(G.get("keywords", []) + G.get("package_keywords", [])),
                 "author": {"@type": "Organization", "name": BRAND, "url": SITE}, "publisher": PUBLISHER, "about": [{"@type": "Place", "name": s}, {"@type": "Thing", "name": "NASCLA contractor licensing exams"}],
                 "citation": [x["url"] for x in srcs], "image": ps[-1]["image"], "mainEntityOfPage": absurl(slug(s) + "/")})
    title = G.get("title") if G.get("title") and len(G["title"]) <= 60 else "%s NASCLA Exam Prep" % s
    desc = G.get("meta_description") or "NASCLA exam prep for %s." % s
    if words < 1600: print("WARNING: %s guide has only %d words" % (s, words))
    GUIDE_STATS.append((s, words, len(srcs)))
    return body, title, desc, [art, faq_ld(qa + faq_pairs)]
GUIDE_STATS = []

# ---------- state hubs: /<state>/ ----------
for s in STATES + [None]:
    rel = "../"; ex = [k for k in EXAM_ORDER if items_for(s, k)]; ps = [p for p in CATALOG if p["state"] == s]
    if not ps: continue
    cards = "".join('<a class="exam" href="%s/"><span class="k">%d PRODUCTS · FROM %s</span><h3>%s</h3><p>%s</p><span class="more">See %s packages →</span></a>'
                    % (k, len(items_for(s, k)), money(price_range(items_for(s, k))[0]), esc(EXAMS[k]["name"]), esc(trim_desc(EXAM_COPY[k]["intro"], 110)), esc(EXAMS[k]["short"])) for k in ex)
    nm = sname(s)
    accept = ("%s accepts the NASCLA commercial building exam in place of its state trade exam; the board's own rules still apply." % s) if s in NCOMM else ""
    body = ('<section class="phead"><div class="wrap">%s<h1>%s NASCLA Exam Prep</h1><p class="lead">%s</p>%s</div></section>'
            % (crumbs_html([("Home", ""), (nm, slug(s) + "/")], rel), esc(nm),
               esc(("NASCLA exam prep for %s: %s. Pick your exam to see the books, tabbed sets, rentals and online courses." % (s, ", ".join(EXAMS[k]["name"].lower() for k in ex))) if s else "Nationwide NASCLA editions that are not tied to one state, plus the multi-state application bundle."),
               takeaways(["%d products for %d exam%s, from %s to %s." % (len(ps), len(ex), "" if len(ex) == 1 else "s", money(price_range(ps)[0]), money(price_range(ps)[1])), accept,
                          "Books ship from our fulfillment center, %s; online courses arrive by email." % FUL["name"]])))
    body += '<section class="sec-tight"><div class="wrap"><div class="exams">%s</div></div></section>' % cards
    if s:
        qa = [("Does %s accept the NASCLA exam?" % s, ("Yes. %s accepts the NASCLA Accredited Examination for Commercial General Building Contractors in place of its state trade exam. You still apply to the %s board and meet its other requirements, which usually include a business and law exam." % (s, s)) if s in NCOMM else
               "%s is not on NASCLA's list of states that accept the commercial building exam in place of the state trade exam. The prep listed here is for the %s exams named below; check the %s licensing board for which exams it requires." % (s, s, s)),
              ("Which NASCLA exams can I prepare for in %s?" % s, "%s. Each has its own page with the books, tabbed sets, rentals and online courses for that exam." % "; ".join("%s (%d products from %s)" % (EXAMS[k]["name"], len(items_for(s, k)), money(price_range(items_for(s, k))[0])) for k in ex)),
              ("How do I register for the NASCLA exam?", "Apply through NASCLA at ned.nascla.org. You must be pre-approved before you can schedule, and then you apply to the %s board with your passing record." % s)]
    else:
        qa = [("What are the nationwide NASCLA editions?", "Prep materials that are not tied to one state: the NASCLA commercial and electrical book packages, highlighted and tabbed sets, rentals and online courses, the Basic edition business and law guide, and the multi-state application bundle.")]
    body = body.replace('<section class="sec-tight"><div class="wrap"><div class="exams">', '<section class="sec-tight" style="padding-top:0"><div class="wrap">%s</div></section><section class="sec-tight"><div class="wrap"><div class="exams">' % quick_answers(qa), 1)
    G = load_guide(slug(s)) if s else None
    if G:
        gbody, gtitle, gdesc, glds = guide_page(s, G, ex, ps, rel, qa)
        write([slug(s)], gbody, gtitle, gdesc, ps[-1]["image"], [crumbs_ld([("Home", ""), (nm, slug(s) + "/")])] + glds, cta=("#packages", "See packages"), route={"state": slug(s)}, priority="0.9")
        continue
    write([slug(s)], body, ("%s NASCLA Exam Prep" % nm) if s else "Nationwide NASCLA Exam Prep Editions", "NASCLA exam prep for %s: %s. %d products from %s." % (nm, ", ".join(EXAMS[k]["short"] for k in ex), len(ps), money(price_range(ps)[0])),
          ps[-1]["image"], [crumbs_ld([("Home", ""), (nm, slug(s) + "/")]), faq_ld(qa)], cta=("#main", "Pick my exam"), route={"state": slug(s)}, priority="0.8")

# ---------- listing pages: /<state>/<exam>/ and product pages ----------
def related_cols(s, k, rel):
    cols = []
    same_state = [x for x in EXAM_ORDER if x != k and items_for(s, x)]
    if same_state: cols.append(("Other %s exams" % sname(s), ['<li><a href="%s%s/%s/">%s %s</a></li>' % (rel, slug(s), x, esc(sname(s)), esc(EXAMS[x]["short"])) for x in same_state]))
    other_states = [x for x in STATES if x != s and items_for(x, k)][:8]
    if other_states: cols.append(("%s in other states" % EXAMS[k]["short"], ['<li><a href="%s%s/%s/">%s</a></li>' % (rel, slug(x), k, esc(x)) for x in other_states] + ['<li><a href="%s%s/">All states for this exam</a></li>' % (rel, k)]))
    if (s, k) in STATE_FAQS: cols.append(("Questions", ['<li><a href="%sfaq/%s/%s/">%s %s FAQ (%d answers)</a></li>' % (rel, slug(s), k, esc(sname(s)), esc(EXAMS[k]["short"]), len(STATE_FAQS[(s, k)])), '<li><a href="%sfaq/">Nationwide NASCLA FAQ</a></li>' % rel]))
    return cols
def cols_html(cols): return "".join('<div class="side-card"><h3>%s</h3><ul>%s</ul></div>' % (esc(h), "".join(items)) for h, items in cols)

USED_TITLES = set()
ABBR = [("Ultimate Exam Prep Rental Package", "Ultimate Rental Package"), ("Highlighted & Tabbed Book Package", "H&T Book Package"), ("Books & Courses Rental Package", "Book + Course Rental"),
        ("Highlighted & Tabbed", "H&T"), ("Business & Law", "B&L"), ("Residential", "Res."), ("The 1 Package: All-Inclusive", "The 1 Package"), ("Live Virtual + Self-Study Training", "Live + Self-Study Training"), ("Online Exam Prep Course", "Online Course")]
def product_title(p):
    """unique title of 60 characters or less: the fullest version that fits wins"""
    E = EXAMS[p["exam"]]; st = p["state"] or "NASCLA"; k = p["kindName"]; ks = k
    for a, b in ABBR: ks = ks.replace(a, b)
    n = re.search(r"-(\d+)$", p["slug"]); tag = (" (Option %s)" % n.group(1)) if n else ""
    sh = E["short"] if p["exam"] != "business-and-law" else ""
    cands = ["%s %s | NASCLA %s" % (st, k, E["short"]), "%s %s %s" % (st, sh, k), "%s %s %s" % (st, sh, ks), "%s %s" % (st, ks)]
    cands = [re.sub(r"\s+", " ", c).strip() + tag for c in cands]
    for c in cands:
        if len(c) <= 60 and c not in USED_TITLES: USED_TITLES.add(c); return c
    c, i = cands[-1], 2
    while c in USED_TITLES: c = "%s (%d)" % (cands[-1], i); i += 1
    USED_TITLES.add(c); return c

def product_page(p, sibs):
    parts = [slug(p["state"]), p["exam"], p["slug"]]; rel = "../../../"; path = "/".join(parts) + "/"; E = EXAMS[p["exam"]]
    full = FULL.get(p["id"], {"html": "", "images": [p["image"]]})
    body_html, dfaq = split_desc(rebrand(full.get("html", "")))
    body_html = re.sub(r"<(/?)h3\b", r"<\1h3", body_html)
    imgs = [u for u in (full.get("images") or [p["image"]]) if u] or [p["image"]]
    v0 = p["variants"][0]; c, n = float(v0.get("compareAt") or 0), float(v0["price"])
    compare = ('<s class="pc-was" id="pWas">%s</s><span class="pc-save" id="pSave">Save %d%%</span>' % (money(c), round((c - n) / c * 100))) if c > n else '<s class="pc-was" id="pWas" hidden></s><span class="pc-save" id="pSave" hidden></span>'
    opts = "".join('<label class="m-opt"><input type="radio" name="v" value="%s"%s><span>%s</span><b>%s%s</b></label>' % (v["id"], " checked" if i == 0 else "", esc(v["title"] if v["title"] != "Default Title" else p["kindName"]), money(v["price"]),
                   ('<s>%s</s>' % money(v["compareAt"])) if v.get("compareAt") and float(v["compareAt"]) > float(v["price"]) else "") for i, v in enumerate(p["variants"]))
    opts_html = ('<fieldset class="opts"><legend>Choose an option</legend>%s</fieldset>' % opts) if len(p["variants"]) > 1 else ""
    thumbs = ('<div class="thumbs">%s</div>' % "".join('<button type="button" data-src="%s" class="%s" aria-label="Show image %d"><img src="%s" alt="" loading="lazy"></button>' % (esc(u), "on" if i == 0 else "", i + 1, esc(u)) for i, u in enumerate(imgs[:6]))) if len(imgs) > 1 else ""
    others = [q for q in sibs if q["id"] != p["id"]]
    related = "".join('<a class="rel" href="%s%s"><img src="%s" alt="" loading="lazy"><span>%s<small>%s</small></span><b>%s</b></a>' % (rel, ppath(q), esc(q["image"]), esc(q["kindName"]), esc(EXAMS[q["exam"]]["short"]), money(q["price"])) for q in sorted(others, key=lambda q: -q["rank"])[:6])
    nm = sname(p["state"])
    tk = takeaways(["%s %s, %s: %s%s." % (nm, E["name"], p["kindName"], money(n), (", down from %s" % money(c)) if c > n else ""),
                    ("%d options to choose from at checkout; the price updates when you pick one." % len(p["variants"])) if len(p["variants"]) > 1 else "",
                    "Online courses arrive by email; books ship from our fulfillment center, %s." % FUL["name"],
                    "Buying does not grant exam eligibility; NASCLA approves you to test and your state board issues the license."])
    pairs = PRODUCT_FAQ + [x for x in dfaq if x[0] not in {q for q, _ in PRODUCT_FAQ}][:12]
    desc = trim_desc(short_desc(p, 40) or p["title"])
    title = product_title(p)
    jsonld = clean({"@context": "https://schema.org", "@type": "Product", "name": p["title"], "image": imgs[:6], "description": p["desc"][:500], "brand": {"@type": "Brand", "name": FUL["name"]},
                    "sku": str(p["id"]), "productID": str(p["id"]), "category": "NASCLA %s Exam Prep" % E["name"], "url": absurl(path),
                    "offers": [{"@type": "Offer", "name": v["title"] if v["title"] != "Default Title" else p["kindName"], "priceCurrency": "USD", "price": v["price"], "availability": "https://schema.org/InStock",
                                "itemCondition": "https://schema.org/NewCondition", "url": absurl(path), "seller": {"@type": "Organization", "name": BRAND}} for v in p["variants"]]})
    crumbs = [("Home", ""), (nm, slug(p["state"]) + "/"), (E["name"], "%s/%s/" % (slug(p["state"]), p["exam"])), (p["kindName"], path)]
    extra_lds = []
    if p["kind"] in ("online-course", "live-training", "practice-questions", "complete-pass-package"):
        extra_lds.append(clean({"@context": "https://schema.org", "@type": "Course", "name": p["title"], "description": trim_desc(p["desc"], 300), "url": absurl(path),
                                "provider": {"@type": "Organization", "name": FUL["name"], "sameAs": FUL["url"]}, "educationalCredentialAwarded": None,
                                "about": "NASCLA %s exam" % E["name"], "teaches": "Preparation for the %s NASCLA %s exam" % (nm if p["state"] else "", E["name"]),
                                "offers": [{"@type": "Offer", "category": "Paid", "price": v["price"], "priceCurrency": "USD", "url": absurl(path)} for v in p["variants"]],
                                "hasCourseInstance": [{"@type": "CourseInstance", "courseMode": "Online" if p["kind"] != "live-training" else "Blended", "courseWorkload": None}]}))
    body = ('<section class="phead" style="padding-bottom:12px"><div class="wrap">%s</div></section><section><div class="wrap"><div class="prod">'
            '<div class="gallery"><div class="main"><img src="%s" alt="%s" fetchpriority="high"></div>%s</div>'
            '<div class="buybox"><div class="meta"><a class="chip" href="%s%s/">%s</a><a class="chip" href="%s%s/">%s</a></div><h1>%s</h1>'
            '<div class="price"><span class="pc-now" data-now>%s</span>%s</div>%s<a class="btn btn-buy" data-buy href="%s" rel="noopener">Buy now</a>'
            '<ul class="assure"><li>%sSecure checkout at %s, our fulfillment center</li><li>%sOnline courses delivered by email after purchase</li><li>%sQuestions? Call <a href="tel:%s">%s</a></li></ul></div></div></div></section>'
            % (crumbs_html(crumbs, rel), esc(imgs[0]), esc(p["title"]), thumbs, rel, slug(p["state"]), esc(nm), rel, "%s/%s" % (slug(p["state"]), p["exam"]), esc(E["short"]), esc(p["title"]),
               money(n), compare, opts_html, buy_url(v0["id"]), ICON_CHECK, esc(FUL["name"]), ICON_CHECK, ICON_CHECK, CFG["phoneTel"], esc(CFG["phone"])))
    body += ('<section class="sec-tight"><div class="wrap"><div class="layout"><div class="main-col">%s<article class="prose"><h2>About this %s</h2>%s</article>'
             '<section class="faq-sec"><h2>Frequently asked questions</h2>%s</section></div><aside class="side-col">%s%s</aside></div></div></section>'
             % (tk, "package" if p["package"] else "product", body_html, faq_html(pairs), ('<div class="side-card"><h3>Other %s %s options</h3>%s</div>' % (esc(nm), esc(E["short"]), related)) if related else "", cols_html(related_cols(p["state"], p["exam"], rel))))
    body += '<div class="stickybar"><span class="pc-now" data-now>%s</span><a class="btn btn-buy" data-buy href="%s" rel="noopener">Buy now</a></div>' % (money(n), buy_url(v0["id"]))
    pjs = json.dumps({"id": p["id"], "variants": p["variants"], "title": p["title"], "state": p["state"], "level": E["name"], "tierName": p["kindName"], "price": p["price"]})
    write(parts, body, title, desc, imgs[0], [jsonld, crumbs_ld(crumbs), faq_ld(pairs)] + extra_lds, cta=(buy_url(v0["id"]), "Buy now"), route={"state": parts[0], "exam": p["exam"]},
          scripts="<script>window.PRODUCT=%s;</script>" % pjs, priority="0.7")

LISTINGS = []
for s in STATES + [None]:
    for k in EXAM_ORDER:
        ps = sorted(items_for(s, k), key=lambda p: (p["rank"], float(p["price"])))
        if not ps: continue
        parts = [slug(s), k]; rel = "../../"; E = EXAMS[k]; nm = sname(s); lo, hi = price_range(ps)
        pk = [p for p in ps if p["package"]]; ad = [p for p in ps if not p["package"]]
        faqs = STATE_FAQS.get((s, k), [])
        chips = "".join('<a class="chip" href="%s%s/%s/"%s>%s <small>%d</small></a>' % (rel, slug(s), x, ' aria-current="page"' if x == k else "", esc(EXAMS[x]["short"]), len(items_for(s, x))) for x in EXAM_ORDER if items_for(s, x))
        ult = next((p for p in pk if p["kind"] == "ultimate"), None); top = next((p for p in reversed(pk)), None)
        tk = takeaways(["%d %s %s products, from %s to %s." % (len(ps), nm, E["name"].lower() if k != "business-and-law" else "business and law", money(lo), money(hi)),
                        ("%s accepts the NASCLA commercial exam: 115 scored questions, 330 minutes, open book, 70%% to pass." % s) if (k == "commercial-general-building-contractor" and s in NCOMM) else (EXAM_COPY[k]["points"][0] if s is None else ""),
                        ("The %s at %s bundles the books with the online course." % (ult["kindName"], money(ult["price"]))) if ult else "",
                        ("%s at %s is the most complete option." % (top["kindName"] if top["kindName"].startswith("The ") else "The " + top["kindName"], money(top["price"]))) if top and top is not ult else "",
                        "Buy now goes straight to secure checkout at our fulfillment center, %s." % FUL["name"]])
        title = "%s NASCLA %s Exam Prep" % (nm, E["name"]) if s else "NASCLA %s Exam Prep, Nationwide" % E["name"]
        if len(title) > 60: title = "%s NASCLA %s Exam Prep" % (nm, E["short"]) if s else "NASCLA %s Prep, Nationwide" % E["short"]
        body = ('<section class="phead"><div class="wrap">%s<h1>%s %s Exam Prep</h1><p class="lead">%s</p><div class="chips" aria-label="Exams in %s">%s</div></div></section>'
                % (crumbs_html([("Home", ""), (nm, slug(s) + "/"), (E["name"], "/".join(parts) + "/")], rel), esc(nm), esc(E["name"] if k != "business-and-law" else "Business and Law"),
                   esc("%s for %s. Choose how much help you want, from a single tabbed guide to the all-inclusive package." % (EXAM_COPY[k]["kicker"], nm) if k != "commercial-general-building-contractor" else "NASCLA Commercial General Building Contractor exam prep for %s. Choose how much help you want, from the online course to The 1 Package with licensing and business setup." % nm),
                   esc(nm), chips))
        guide = []
        for kk, label in (("online-course", "the online course"), ("highlighted-tabbed", "the highlighted and tabbed book package"), ("ultimate", "the Ultimate rental (books plus course)"), ("the-1-package", "The 1 Package (adds licensing and business setup)")):
            q0 = next((p for p in pk if p["kind"] == kk), None)
            if q0: guide.append("%s at %s" % (label, money(q0["price"])))
        exname = E["name"].lower() if k != "business-and-law" else "business and law"
        qa = [("How much does %s %s exam prep cost?" % (nm, exname), "%s %s prep runs from %s to %s across %d products%s." % (nm, exname, money(lo), money(hi), len(ps), (": " + "; ".join("%s %s" % (p["kindName"], money(p["price"])) for p in ps[:8])) if len(ps) <= 8 else ""))]
        if guide: qa.append(("Which %s %s package should I choose?" % (nm, exname), "Pick by how much help you want: %s. Every option is built for the open-book exam." % "; ".join(guide)))
        if k == "commercial-general-building-contractor" and s in NCOMM:
            qa.append(("Can I use the NASCLA exam for a %s license?" % s, "Yes. %s accepts the NASCLA commercial exam in place of its trade exam; the board's application and business and law requirements still apply." % s))
        elif k == "business-and-law":
            qa.append(("Which book is the %s business and law exam based on?" % nm, "Most states write it from NASCLA's Contractor's Guide to Business, Law and Project Management in the state's own edition. The editions we carry for %s are listed below; confirm the edition in your candidate bulletin." % nm))
        body += '<section class="sec-tight" style="padding-top:8px"><div class="wrap">%s%s' % (quick_answers(qa), tk)
        if pk: body += '<div class="group-h"><h2>Packages</h2><p>%d options, smallest to most complete</p></div><div class="grid" id="rail">%s</div>' % (len(pk), "".join(card(p, rel) for p in pk))
        if ad: body += '<div class="group-h"><h2>%s</h2><p>%d item%s</p></div><div class="rows">%s</div>' % ("Books, tabs and flash cards" if pk else "Books and tabs", len(ad), "" if len(ad) == 1 else "s", "".join(row(p, rel) for p in ad))
        body += "</div></section>"
        if faqs:
            body += ('<section class="sec-tight"><div class="wrap"><div class="layout"><div class="main-col"><h2 style="font-size:28px">%s %s questions</h2>%s<p style="margin-top:16px"><a href="%sfaq/%s/%s/">All %d answers for %s %s</a></p></div><aside class="side-col">%s</aside></div></div></section>'
                     % (esc(nm), esc(E["short"]), faq_html(faqs[:6]), rel, slug(s), k, len(faqs), esc(nm), esc(E["short"]), cols_html(related_cols(s, k, rel))))
        else:
            body += '<section class="sec-tight"><div class="wrap"><div class="layout"><div class="main-col"><h2 style="font-size:28px">Questions</h2>%s</div><aside class="side-col">%s</aside></div></div></section>' % (faq_html(PRODUCT_FAQ), cols_html(related_cols(s, k, rel)))
        lpairs = qa + (faqs[:6] or PRODUCT_FAQ)
        write(parts, body, title, "%s %s exam prep: %d products from %s to %s. Book packages, highlighted and tabbed sets, rentals and online courses. One click to checkout." % (nm, E["name"].lower(), len(ps), money(lo), money(hi)),
              ps[-1]["image"], [crumbs_ld([("Home", ""), (nm, slug(s) + "/"), (E["name"], "/".join(parts) + "/")]),
              {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": absurl("/".join(parts) + "/"), "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": absurl(ppath(p)), "name": p["title"]} for i, p in enumerate(ps)]}},
              faq_ld(lpairs)], cta=("#rail" if pk else "#main", "See packages"), route={"state": slug(s), "exam": k}, scripts='<script src="%sshared/catalog.js" defer></script>' % rel, priority="0.9")
        LISTINGS.append((s, k))
        for p in ps: product_page(p, ps)

# ---------- FAQ ----------
total_state_q = sum(len(v) for v in STATE_FAQS.values())
for (s, k), pairs in sorted(STATE_FAQS.items(), key=lambda kv: (kv[0][0] is None, kv[0][0] or "", EXAMS[kv[0][1]]["order"])):
    parts = ["faq", slug(s), k]; rel = "../../../"; nm = sname(s); E = EXAMS[k]
    buckets = [("exam", "The exam", r"open book|question|score|pass|time|minutes|hours|format|administer|vendor|psi|prometric|pearson|schedul|retake|fail|edition|reference|book"),
               ("license", "Licensing", r"licens|board|experience|apply|application|eligib|reciproc|renew|insurance|bond|financial|contractor|business|law")]
    used, secs = set(), []
    for sid, name, rx in buckets:
        sel = [x for x in pairs if x not in used and re.search(rx, x[0], re.I)]
        if sel: secs.append((sid, name, sel)); used.update(sel)
    rest = [x for x in pairs if x not in used]
    if rest: secs.append(("more", "More questions", rest))
    jump = "".join('<a class="chip" href="#%s">%s <small>%d</small></a>' % (sid, esc(n), len(sel)) for sid, n, sel in secs)
    body = ('<section class="phead"><div class="wrap">%s<h1>%s %s exam: frequently asked questions</h1><p class="lead">%d answers about the %s %s exam and license, compiled from our product descriptions for this exam.</p><div class="jump">%s</div></div></section>'
            % (crumbs_html([("Home", ""), ("FAQ", "faq/"), ("%s %s" % (nm, E["short"]), "/".join(parts) + "/")], rel), esc(nm), esc(E["name"]), len(pairs), esc(nm), esc(E["name"].lower()), jump))
    body += '<section class="sec-tight" style="padding-top:0"><div class="wrap"><div class="layout"><div class="main-col">%s</div><aside class="side-col"><div class="side-card"><h3>Ready to study?</h3><ul><li><a href="%s%s/%s/">%s %s packages</a></li></ul></div>%s</aside></div></div></section>' % (
        "".join('<section class="faq-sec" aria-labelledby="%s"><h2 id="%s">%s</h2>%s</section>' % (sid, sid, esc(n), faq_html(sel, i == 0)) for i, (sid, n, sel) in enumerate(secs)), rel, slug(s), k, esc(nm), esc(E["short"]), cols_html(related_cols(s, k, rel)))
    title = "%s NASCLA %s FAQ" % (nm, E["short"])
    write(parts, body, title, "%d answers about the %s %s exam: open-book rules, reference books, licensing steps, the business and law exam and more." % (len(pairs), nm, E["name"].lower()),
          None, [crumbs_ld([("Home", ""), ("FAQ", "faq/"), ("%s %s" % (nm, E["short"]), "/".join(parts) + "/")]), faq_ld(pairs[:80])], cta=("%s/%s/" % (slug(s), k), "See packages"), current="faq", priority="0.5")
gen_pairs = [(q, a) for c in GEN_FAQ for q, a in c["items"]]
secs = "".join('<section class="faq-sec" aria-labelledby="%s"><h2 id="%s">%s</h2>%s</section>' % (c["slug"], c["slug"], esc(c["name"]), faq_html(c["items"], i == 0)) for i, c in enumerate(GEN_FAQ))
state_links = "".join('<li><a href="%s/%s/">%s</a><span>%s</span></li>' % (slug(s), [k for k in EXAM_ORDER if (s, k) in STATE_FAQS][0], esc(sname(s)), "".join('<a href="%s/%s/">%s %d</a>' % (slug(s), k, esc(EXAMS[k]["short"]), len(STATE_FAQS[(s, k)])) for k in EXAM_ORDER if (s, k) in STATE_FAQS)) for s in STATES + [None] if any((s, k) in STATE_FAQS for k in EXAM_ORDER))
jump = "".join('<a class="chip" href="#%s">%s <small>%d</small></a>' % (c["slug"], esc(c["name"]), len(c["items"])) for c in GEN_FAQ) + '<a class="chip" href="#states">State by state <small>%d</small></a>' % total_state_q
body = ('<section class="phead"><div class="wrap">%s<h1>NASCLA exam FAQ</h1><p class="lead">%d answers about NASCLA exams: what NASCLA is, the commercial exam, licensing, studying and ordering, plus %d state-specific answers.</p><div class="jump">%s</div></div></section>'
        % (crumbs_html([("Home", ""), ("FAQ", "faq/")], "../"), len(gen_pairs) + total_state_q, total_state_q, jump))
body += '<section class="sec-tight" style="padding-top:0"><div class="wrap" style="max-width:900px">%s<section class="faq-sec" aria-labelledby="states"><h2 id="states">State by state</h2><p style="color:var(--muted)">Answers for each state and exam, taken from our product descriptions: who issues the license, open-book rules, reference books and the business and law exam.</p><ul class="states">%s</ul></section></div></section>' % (secs, state_links)
body += final_cta("Ready to study?", "Pick your exam and state.", "Every package is built for the open-book format.", "../#exams", "Find my exam")
write(["faq"], body, "NASCLA Exam FAQ: %d Answers" % (len(gen_pairs) + total_state_q), "%d answers about NASCLA exams: the commercial exam format, which states accept it, licensing, open-book study and ordering, plus state-specific answers." % (len(gen_pairs) + total_state_q),
      None, [crumbs_ld([("Home", ""), ("FAQ", "faq/")]), faq_ld(gen_pairs)], cta=("#exams", "Find my exam"), current="faq", priority="0.7")

# ---------- blog ----------
shutil.rmtree(os.path.join(ROOT, "blog"), ignore_errors=True); shutil.rmtree(os.path.join(ROOT, "pages"), ignore_errors=True)
def nice(d):
    try: return datetime.date.fromisoformat(d[:10]).strftime("%B %-d, %Y")
    except Exception: return d
def post_card(q, rel):
    img = ('<img src="%s" alt="" loading="lazy">' % esc(q["image"])) if q["image"] else '<div class="noimg">%s</div>' % esc(q["title"][:60])
    return '<a class="card" href="%sblog/%s/">%s<div class="card-body"><p class="post-meta"><time datetime="%s">%s</time><span>%d min read</span></p><h2>%s</h2><p>%s</p></div></a>' % (rel, q["slug"], img, q["date"], nice(q["date"]), max(1, round(q["words"] / 220)), esc(q["title"]), esc(q["excerpt"]))
all_tags = sorted({t for q in POSTS for t in q["tags"]}, key=str.lower)
def blog_index(parts, posts, tag=None):
    rel = "../" * len(parts); path = "/".join(parts) + "/"
    h1 = ("Posts tagged “%s”" % tag) if tag else "The NASCLA Exam Prep Blog"
    tags = ('<div class="chips">%s</div>' % "".join('<a class="chip" href="%sblog/tag/%s/"%s>%s</a>' % (rel, blogkit.slugify(t), ' aria-current="page"' if t == tag else "", esc(t)) for t in all_tags)) if all_tags else ""
    body = ('<section class="phead"><div class="wrap">%s<h1>%s</h1><p class="lead">%s</p>%s</div></section><section class="sec-tight" style="padding-top:0"><div class="wrap">%s</div></section>'
            % (crumbs_html([("Home", ""), ("Blog", "blog/")] + ([(tag, path)] if tag else []), rel), esc(h1), "Study plans for open-book NASCLA exams, state licensing steps, business and law tips and news, written by the people who make the prep." if not tag else "%d posts." % len(posts),
               tags, ('<div class="post-grid">%s</div>' % "".join(post_card(q, rel) for q in posts)) if posts else '<p class="empty">No posts yet. The first one is on its way.</p>'))
    body += final_cta("Ready to study?", "Pick your exam and state.", "Book packages, tabbed sets, rentals and online courses.", rel + "#exams", "Find my exam")
    lds = [crumbs_ld([("Home", ""), ("Blog", "blog/")] + ([(tag, path)] if tag else [])), clean({"@context": "https://schema.org", "@type": "Blog", "name": h1, "url": absurl(path), "publisher": {"@type": "Organization", "name": BRAND},
           "blogPost": [{"@type": "BlogPosting", "headline": q["title"], "url": absurl("blog/%s/" % q["slug"]), "datePublished": q["date"]} for q in posts[:20]]})]
    write(parts, body, ("Posts tagged %s | %s" % (tag, BRAND)) if tag else "NASCLA Exam Prep Blog", "Study plans, licensing steps and exam strategy for NASCLA commercial, electrical and business and law exams.", None, lds, noindex=bool(tag), cta=("#exams" if False else "../#exams", "Find my exam"), current="blog", priority="0.6")
blog_index(["blog"], POSTS)
for t in all_tags: blog_index(["blog", "tag", blogkit.slugify(t)], [q for q in POSTS if t in q["tags"]], t)
for q in POSTS + PAGES:
    is_page = q.get("kind") == "page"; parts = ["pages" if is_page else "blog", q["slug"]]; rel = "../../"; path = "/".join(parts) + "/"
    st = q.get("state") if q.get("state") in STATES else None
    rel_posts = [r for r in POSTS if r["slug"] != q["slug"] and set(r["tags"]) & set(q["tags"])][:3] or [r for r in POSTS if r["slug"] != q["slug"]][:3]
    hero = ('<figure class="hero-img"><img src="%s" alt="%s"></figure>' % (esc(q["image"]), esc(q["title"]))) if q["image"] and q["image"] not in q["html"] else ""
    cr = [("Home", ""), (q["title"], path)] if is_page else [("Home", ""), ("Blog", "blog/"), (q["title"], path)]
    body = ('<section class="phead"><div class="wrap" style="max-width:860px">%s<h1>%s</h1>%s</div></section><section class="sec-tight post" style="padding-top:0"><div class="wrap" style="max-width:960px">%s%s<article class="post-body">%s</article></div></section>'
            % (crumbs_html(cr, rel), esc(q["title"]), "" if is_page else '<p class="post-meta"><time datetime="%s">%s</time><span>%d min read</span>%s</p>' % (q["date"], nice(q["date"]), max(1, round(q["words"] / 220)), ("<span>%s</span>" % esc(q["author"])) if q["author"] else ""),
               hero, takeaways(q.get("takeaways") or []), q["html"]))
    body += final_cta(("%s exams" % st) if st else "Ready to study?", ("See the %s NASCLA packages." % st) if st else "Pick your exam and state.", "Book packages, tabbed sets, rentals and online courses.", (rel + slug(st) + "/") if st else rel + "#exams", ("See %s" % st) if st else "Find my exam")
    if rel_posts and not is_page: body += '<section class="sec-tight"><div class="wrap"><h2 style="font-size:26px">Keep reading</h2><div class="post-grid">%s</div></div></section>' % "".join(post_card(r, rel) for r in rel_posts)
    art = clean({"@context": "https://schema.org", "@type": "Article" if is_page else "BlogPosting", "headline": q["title"][:110], "description": q["excerpt"], "image": [q["image"]] if q["image"] else None, "datePublished": q["date"], "dateModified": q["updated"],
                 "author": {"@type": "Organization" if not q["author"] or q["author"] == BRAND else "Person", "name": q["author"] or BRAND}, "publisher": {"@type": "Organization", "name": BRAND, "logo": {"@type": "ImageObject", "url": CFG.get("logo")}},
                 "mainEntityOfPage": absurl(path), "url": absurl(path), "wordCount": q["words"], "keywords": ", ".join(q["tags"]) or None, "inLanguage": "en-US"})
    write(parts, body, q.get("meta_title") or (q["title"] if len(q["title"]) + len(BRAND) + 3 > 60 else "%s | %s" % (q["title"], BRAND)), q.get("meta_description") or q["excerpt"], q["image"] or None, [crumbs_ld(cr), art], cta=(rel + "#exams", "Find my exam"), current="blog", priority="0.7")
rpath = os.path.join(ROOT, "content", "redirects.json")
if os.path.exists(rpath):
    try: RED = json.load(open(rpath, encoding="utf-8"))
    except Exception: RED = {}
    for old, new in RED.items():
        old, new = old.strip("/"), new.strip("/")
        if not old or old == new or os.path.exists(os.path.join(ROOT, *old.split("/"), "index.html")): continue
        tgt = absurl(new + "/"); os.makedirs(os.path.join(ROOT, *old.split("/")), exist_ok=True)
        open(os.path.join(ROOT, *old.split("/"), "index.html"), "w", encoding="utf-8").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title><meta name="robots" content="noindex"><link rel="canonical" href="%s"><meta http-equiv="refresh" content="0; url=%s"></head><body><p>Moved to <a href="%s">%s</a>.</p></body></html>' % (esc(tgt), esc(tgt), esc(tgt), esc(tgt)))
os.makedirs(os.path.join(ROOT, "blog"), exist_ok=True)
items = "".join('<item><title>%s</title><link>%s</link><guid isPermaLink="true">%s</guid><pubDate>%s</pubDate><description>%s</description></item>\n' % (esc(q["title"]), absurl("blog/%s/" % q["slug"]), absurl("blog/%s/" % q["slug"]), datetime.datetime.fromisoformat(q["date"][:10]).strftime("%a, %d %b %Y 09:00:00 -0500"), esc(q["excerpt"])) for q in POSTS[:30])
open(os.path.join(ROOT, "blog", "feed.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>%s Blog</title><link>%s</link><description>NASCLA exam prep study tips, licensing steps and news.</description><language>en-us</language>\n%s</channel></rss>\n' % (esc(BRAND), absurl("blog/"), items))
open(os.path.join(ROOT, "blog", "posts.json"), "w", encoding="utf-8").write(json.dumps([{k: q[k] for k in ("slug", "title", "date", "updated", "excerpt", "image", "tags", "state", "level", "author", "words")} for q in POSTS], ensure_ascii=False))

# ---------- search ----------
write(["search"], '<section class="phead search-page"><div class="wrap"><h1>Search</h1><form id="searchPage" class="srch-form" role="search"><label class="sr-only" for="sp">Search</label><input class="srch-q" id="sp" name="q" type="search" placeholder="State, exam or product" autocomplete="off"><button class="btn btn-buy" type="submit">Search</button></form><div id="searchOut" class="srch-res"></div></div></section>',
      "Search | %s" % BRAND, "Search NASCLA exam prep by state, exam or product.", None, noindex=True, cta=("../#exams", "Find my exam"), sitemap=False, scripts='<script src="../shared/catalog.js"></script>')
GENERATED.append("search")
with open(manifest, "w") as f: f.write("\n".join(sorted(set(GENERATED))) + "\n")

# ---------- 404 ----------
known = sorted({slug(s) for s in STATES} | {NATIONAL} | set(EXAM_ORDER) | {"faq", "blog", "search"})
nf = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Page not found | %s</title><meta name="robots" content="noindex">%s<link rel="stylesheet" href="%sshared/site.css"></head>'
      '<body><main id="main" class="sec"><div class="wrap" style="max-width:720px"><span class="eyebrow">404</span><h1>That page moved or never existed.</h1><p style="color:var(--muted)">Taking you to the closest match. If nothing happens, start from the <a href="%s">home page</a>.</p></div></main>'
      '<script>(function(){var K=%s;var parts=location.pathname.split("/").filter(Boolean).map(function(x){return x.toLowerCase();});for(var i=0;i<parts.length;i++){if(K.indexOf(parts[i])>-1){var pre="/"+parts.slice(0,i).join("/");if(pre!=="/")pre+="/";var tgt=pre+parts[i]+"/";if(K.indexOf(parts[i+1])>-1)tgt+=parts[i+1]+"/";location.replace(tgt);return;}}})();</script></body></html>'
      % (esc(BRAND), FONTS, SITE or "/", SITE or "/", json.dumps(known)))
open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(nf)

# ---------- icons, social card, manifest ----------
open(os.path.join(ROOT, "shared", "favicon.svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0B0F1A"/><circle cx="32" cy="32" r="20" fill="none" stroke="#4C8DFF" stroke-width="5"/><path d="M32 20v12l9 5" fill="none" stroke="#EEF1F8" stroke-width="5" stroke-linecap="round"/></svg>')
try:
    from PIL import Image, ImageDraw, ImageFont
    def font(sz, bold=True):
        for f in (("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
            if os.path.exists(f): return ImageFont.truetype(f, sz)
        return ImageFont.load_default()
    def clock(d, cx, cy, r, w):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(76, 141, 255), width=w)
        d.line([(cx, cy - r * .58), (cx, cy)], fill=(238, 241, 248), width=w); d.line([(cx, cy), (cx + r * .42, cy + r * .25)], fill=(238, 241, 248), width=w)
    for name, size in (("favicon.png", 64), ("apple-touch-icon.png", 180), ("logo-mark.png", 512)):
        im = Image.new("RGBA", (size, size), (11, 15, 26, 255)); clock(ImageDraw.Draw(im), size / 2, size / 2, size * .32, max(3, size // 13)); im.save(os.path.join(ROOT, "shared", name))
    lg = Image.new("RGB", (1200, 630), (11, 15, 26)); d = ImageDraw.Draw(lg); clock(d, 170, 315, 90, 16)
    d.text((310, 200), "Pass Your NASCLA", font=font(76), fill=(238, 241, 248)); d.text((310, 290), "Exam Prep", font=font(76), fill=(76, 141, 255))
    d.text((312, 400), "Commercial, electrical and business & law exams", font=font(30, False), fill=(179, 188, 208))
    d.text((312, 445), "115 scored questions  ·  330 minutes  ·  open book", font=font(26, False), fill=(141, 182, 255))
    d.text((312, 560), "Fulfilled by %s" % FUL["name"], font=font(22, False), fill=(141, 151, 174))
    lg.save(os.path.join(ROOT, "shared", "logo.png"), optimize=True)
except Exception as e: print("icons skipped:", e)
open(os.path.join(ROOT, "manifest.webmanifest"), "w").write(json.dumps({"name": BRAND, "short_name": "NASCLA Prep", "start_url": "./", "display": "browser", "background_color": "#0B0F1A", "theme_color": "#0B0F1A",
     "icons": [{"src": "shared/logo-mark.png", "sizes": "512x512", "type": "image/png"}, {"src": "shared/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}, {"src": "shared/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}, indent=1))

# ---------- robots.txt, llms.txt, agents.md, sitemap.xml ----------
bots = ["GPTBot", "ChatGPT-User", "OAI-SearchBot", "ClaudeBot", "Claude-User", "anthropic-ai", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bytespider", "CCBot", "Amazonbot", "meta-externalagent"]
rb = ("# robots.txt for %s (%s)\n# Search engines and AI assistants are both welcome. Internal search, raw data and build files are held back.\n\n" % (BRAND, (SITE or "/").rstrip("/"))
      + "User-agent: *\nAllow: /\nDisallow: /search/\nDisallow: /store/\nDisallow: /data/\nDisallow: /tools/\nDisallow: /*?q=\n\n# Named so the allow is explicit for AI crawlers.\n" + "".join("User-agent: %s\nAllow: /\n\n" % b for b in bots))
if SITE: rb += "Sitemap: %ssitemap.xml\n# Blog: %sblog/ (RSS at %sblog/feed.xml). FAQ: %sfaq/\n# Guides for AI assistants: %sllms.txt and %sagents.md\n" % (SITE, SITE, SITE, SITE, SITE, SITE)
open(os.path.join(ROOT, "robots.txt"), "w").write(rb)
kinds_desc = "Package types, smallest to most complete: Online Exam Prep Course, Exam Book Package, Highlighted & Tabbed Book Package, Books & Courses Rental Package, Ultimate Exam Prep Rental Package (books + online course), The 1 Package (all-inclusive, adds licensing and business setup). Books, pre-printed tabs and flash cards are also sold on their own."
llm = ["# %s" % BRAND, "", "> NASCLA exam prep: the NASCLA Accredited Examination for Commercial General Building Contractors (accepted in 16 states and the U.S. Virgin Islands), NASCLA accredited electrical exams (master electrical contractor, journeyman electrician, residential electrical contractor) and state business and law exams. %d products across %d states plus nationwide editions. Buy buttons go straight to secure checkout; orders are fulfilled by %s. Phone %s, email %s." % (len(CATALOG), len(STATES), FUL["name"], CFG["phone"], CFG["email"]), "",
       "## How the site is organised", "", "- `/<exam>/` lists the states that carry an exam. Exam slugs: %s." % ", ".join(EXAM_ORDER), "- `/<state>/` lists a state's exams (multi-word states use a dash, e.g. `/north-carolina/`; `/national/` holds nationwide editions).",
       "- `/<state>/<exam>/` lists that state's products for the exam.", "- `/<state>/<exam>/<product>/` is a full product page with price, options, description, FAQ and a Buy now button.", "- " + kinds_desc, "", "## Exams", ""]
llm += ["- [NASCLA %s exam prep](%s): %s" % (EXAMS[k]["name"], absurl(k + "/index.md"), trim_desc(EXAM_COPY[k]["intro"], 140)) for k in EXAM_ORDER]
llm += ["", "## State pages", ""] + ["- [%s NASCLA exam prep](%s)" % (sname(s), absurl(slug(s) + "/index.md")) for s in STATES + [None]]
llm += ["", "## State and exam pages", ""] + ["- [%s %s](%s): %d products from %s" % (sname(s), EXAMS[k]["name"], absurl("%s/%s/index.md" % (slug(s), k)), len(items_for(s, k)), money(price_range(items_for(s, k))[0])) for s, k in LISTINGS]
if POSTS: llm += ["", "## Blog", "", "- [All posts](%s)" % absurl("blog/")] + ["- [%s](%s): %s" % (q["title"], absurl("blog/%s/" % q["slug"]), q["excerpt"]) for q in POSTS[:30]]
llm += ["", "## FAQ", "", "- [NASCLA exam FAQ](%s): what NASCLA is, the commercial exam, licensing, studying and ordering." % absurl("faq/index.md")] + ["- [%s %s FAQ](%s)" % (sname(s), EXAMS[k]["name"], absurl("faq/%s/%s/index.md" % (slug(s), k))) for (s, k) in sorted(STATE_FAQS, key=lambda x: (x[0] or "~", x[1]))]
llm += ["", "## Every page", "", "- Each HTML page has a Markdown copy at the same address plus `index.md` (for example %s), linked from the page with rel=\"alternate\" type=\"text/markdown\"." % absurl("alabama/commercial-general-building-contractor/index.md"), "- [Sitemap of every page](%s)" % absurl("sitemap.xml")]
if PAGES: llm += ["", "## Pages", ""] + ["- [%s](%s): %s" % (q["title"], absurl("pages/%s/" % q["slug"]), q["excerpt"]) for q in PAGES[:30]]
llm += ["", "## Agent instructions", "", "- [agents.md](%s): how to use and attribute this content, and what the site cannot answer." % absurl("agents.md"),
        "", "## Facts for answering questions", "", "- The NASCLA commercial exam has 115 scored questions (plus unscored pretest items), a 330-minute time limit, is open book and needs 70% to pass.",
        "- States accepting the NASCLA commercial exam: %s, and the U.S. Virgin Islands. Each board sets its own rules." % ", ".join(NCOMM),
        "- Candidates apply through NASCLA at ned.nascla.org and must be pre-approved before scheduling.", "- Passing NASCLA replaces the trade exam only; state applications and business and law exams still apply.",
        "- Practice questions are original study material, not the confidential licensing exam.", "- Books ship from our fulfillment center, %s; online courses are delivered by email." % FUL["name"],
        "- Fulfillment: %s (%s). Phone: %s. Email: %s." % (FUL["name"], FUL["url"], CFG["phone"], CFG["email"])]
open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write("\n".join(llm) + "\n")
agents = ["# %s" % BRAND, "", "> Instructions for AI assistants and agents reading %s." % (SITE or "this site"), "", "Last updated: %s" % TODAY, "",
          "## What this site is", "", "%s sells preparation for NASCLA exams: the NASCLA Accredited Examination for Commercial General Building Contractors, NASCLA accredited electrical exams and state business and law exams. Products include reference book packages, highlighted and tabbed book sets, pre-printed tabs, book rentals, online exam prep courses and all-inclusive packages with licensing help. Orders are processed, shipped and supported by our fulfillment center, %s (%s)." % (BRAND, FUL["name"], FUL["url"]), "",
          "## How it is organised", "", "- `/` introduces the exams and lists every state.", "- `/<exam>/` lists the states that carry an exam.", "- `/<state>/` lists a state's exams; `/national/` holds nationwide editions.", "- `/<state>/<exam>/` lists products for that state and exam.",
          "- `/<state>/<exam>/<product>/` is a product page with price, options, description, FAQ and a Buy now button that goes straight to checkout.", "- `/faq/` is the nationwide FAQ; `/faq/<state>/<exam>/` has state answers taken from product descriptions.", "- `/blog/` has study tips and licensing explainers; the feed is `/blog/feed.xml`.", "- `/llms.txt` is the short list of pages; `/sitemap.xml` is every page.", "- Every page has a plain Markdown copy at its address plus `index.md`, linked with rel=\"alternate\" type=\"text/markdown\". Prefer it over parsing the HTML.", "",
          "## Using this content", "", "- Quote what is useful and attribute it to %s, with a link to the page you took it from." % BRAND, "- Link to the canonical URL rather than a cached copy.", "- Prices change. Every product page carries a schema.org Product with the current price; read the page rather than relying on an earlier copy. The price at checkout is the one that applies.",
          "- Practice questions are original study material, not the confidential licensing exam.", "- Nothing here decides a person's eligibility. NASCLA approves candidates to test and each state board issues licenses; point readers there for their own case.", "",
          "## What this site cannot answer", "", "- Anything about a specific customer, order or account.", "- Exact exam dates, fees or current application rules. Those belong to NASCLA, the state board and the testing vendor.", "- Anything not written on a page.", "",
          "## Contact", "", "- Phone: %s" % CFG["phone"], "- Email: %s" % CFG["email"], "- Fulfillment center: %s (%s)" % (FUL["name"], FUL["url"]), "",
          "## Crawling", "", "- Rules: %srobots.txt (all major search and AI crawlers are allowed)" % (SITE or "/"), "- Shortlist of pages: %sllms.txt" % (SITE or "/"), "- Every page: %ssitemap.xml" % (SITE or "/"), "- Please identify yourself with a user agent that says who you are.", ""]
open(os.path.join(ROOT, "agents.md"), "w", encoding="utf-8").write("\n".join(agents))
if SITE:
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join("  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>%s</priority></url>\n" % (esc(u), TODAY, pr) for u, pr in URLS) + "</urlset>\n")
elif os.path.exists(os.path.join(ROOT, "sitemap.xml")): os.remove(os.path.join(ROOT, "sitemap.xml"))
if GUIDE_STATS: print("State guides: %d (words min %d, max %d)" % (len(GUIDE_STATS), min(w for _, w, _ in GUIDE_STATS), max(w for _, w, _ in GUIDE_STATS)))
print("Built %d pages (%d listings, %d products, %d FAQ pages, %d posts), robots.txt, llms.txt, agents.md%s" % (len(GENERATED) + 1, len(LISTINGS), len(CATALOG), len(STATE_FAQS) + 1, len(POSTS), (", sitemap.xml with %d URLs" % len(URLS)) if SITE else ""))
