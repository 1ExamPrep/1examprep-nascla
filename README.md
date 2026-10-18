# Pass Your NASCLA Exam Prep

Static site for passyournasclaexamprep.com: NASCLA exam prep for the Commercial General Building Contractor
exam, NASCLA electrical exams (master, journeyman, residential) and state business and law exams.
Every product comes from the 1 Exam Prep Shopify store (all products with NASCLA in the title).
Buy now buttons go straight to Shopify checkout.

## Build

```bash
pip install pillow
python3 tools/build_catalog.py data/shopify/nascla-products.json   # or tools/sync_shopify.py with Shopify credentials
python3 build.py
python3 -m http.server 8000      # open http://localhost:8000
```

## How pages are organised

| URL | Page |
|---|---|
| `/` | Home |
| `/<exam>/` | One page per exam, listing its states |
| `/<state>/` | One page per state (`/national/` for nationwide editions) |
| `/<state>/<exam>/` | Packages for that state and exam |
| `/<state>/<exam>/<product>/` | Product page |
| `/faq/`, `/faq/<state>/<exam>/` | Nationwide FAQ, state answers from the product descriptions |
| `/blog/` | Blog (posts in `content/posts/*.md`, see `tools/blogkit.py`) |

SEO built in on every build: canonical tags, `sitemap.xml`, `robots.txt` (AI crawlers allowed), `llms.txt`,
`agents.md`, Open Graph and Twitter cards, and schema.org Organization, WebSite, WebPage, BreadcrumbList,
CollectionPage, Product, FAQPage and BlogPosting markup.

## Where things live

```
site-config.json         brand, domain, contact, dashboard hook
build.py                 generates every page; copy and schema text live here
shared/site.css, site.js theme and behaviour (search, gallery, option picker)
shared/catalog.js        generated product catalog
store/products-full.json generated product descriptions
tools/build_catalog.py   sorts products into state / exam / package type (edit exam_of, kind_of)
tools/sync_shopify.py    pulls products from Shopify and rebuilds
content/faq-general.json nationwide FAQ
content/posts/*.md       blog posts
data/shopify/            raw Shopify export (2026-10-18)
```

## Going live on the domain

1. DNS: four `A` records on `passyournasclaexamprep.com` to `185.199.108.153`, `185.199.109.153`,
   `185.199.110.153`, `185.199.111.153`, and a `CNAME` for `www` to `1examprep.github.io`.
2. Repo Settings > Pages > Custom domain: `passyournasclaexamprep.com`, then Enforce HTTPS once offered.
3. In `site-config.json` set `siteUrl` and `logo` to the domain, then push. Canonicals, sitemap, robots,
   llms.txt and agents.md all switch over on the next build.

## Dashboard note

The site dashboard's Shopify sync (`server/shopify.js`) is written for the electrician catalog. Do not point
it at this repo until its catalog rules match `tools/build_catalog.py`, or it will overwrite `shared/catalog.js`
with the wrong structure. The weekly GitHub sync in `.github/workflows/sync-shopify.yml` uses this repo's rules
and runs once the `SHOPIFY_STORE_DOMAIN` and `SHOPIFY_ADMIN_TOKEN` secrets are added.
