#!/usr/bin/env python3
"""Pull every NASCLA product from Shopify, rebuild the catalog, and report whether anything changed.

Needs these environment variables (GitHub Actions gets them from repository secrets):
  SHOPIFY_STORE_DOMAIN   e.g. brown-1exam.myshopify.com
  and either
  SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET   Dev Dashboard app credentials (the secret starts with shpss_).
                         The app must be installed on the store with read_products. A 24-hour access token is
                         requested on every run with the client credentials grant.
  or
  SHOPIFY_ADMIN_TOKEN    an existing Admin API access token (older custom apps)

Optional:
  SHOPIFY_QUERY          product search (default: title:*NASCLA*)
  SHOPIFY_COLLECTION_ID  pull one collection instead of the search above
  SHOPIFY_API_VERSION    default 2025-07

Usage:  python3 tools/sync_shopify.py     exit 0 = unchanged, exit 3 = catalog changed (site rebuilt), other = error
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = os.environ.get("SHOPIFY_STORE_DOMAIN", "").strip()
TOKEN = os.environ.get("SHOPIFY_ADMIN_TOKEN", "").strip()
CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
SEARCH = os.environ.get("SHOPIFY_QUERY", "title:*NASCLA*").strip()
COLL = os.environ.get("SHOPIFY_COLLECTION_ID", "").strip()
VER = os.environ.get("SHOPIFY_API_VERSION", "2025-07").strip()
BASE = DOMAIN if DOMAIN.startswith("http") else "https://" + DOMAIN
if DOMAIN and CLIENT_ID and CLIENT_SECRET:
    # client credentials grant: trade the app's client ID and secret for a 24-hour access token
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}).encode()
    req = urllib.request.Request(BASE + "/admin/oauth/access_token", data=body, headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: TOKEN = json.load(r).get("access_token", "")
    except urllib.error.HTTPError as e:
        print("Shopify refused the client credentials (%s): %s" % (e.code, e.read().decode()[:300])); sys.exit(2)
    if not TOKEN: print("No access token returned for the client credentials"); sys.exit(2)
    print("got a 24-hour access token from the client credentials")
if not DOMAIN or not TOKEN:
    print("Set SHOPIFY_STORE_DOMAIN plus SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET (or SHOPIFY_ADMIN_TOKEN)"); sys.exit(2)

FIELDS = """edges { node {
      id title handle status productType vendor tags onlineStoreUrl descriptionHtml
      featuredImage { url altText }
      images(first: 6) { edges { node { url altText } } }
      priceRangeV2 { minVariantPrice { amount } maxVariantPrice { amount } }
      variants(first: 10) { edges { node { id title price compareAtPrice availableForSale } } }
    } }
    pageInfo { hasNextPage endCursor }"""
Q_SEARCH = "query($q: String!, $first: Int!, $after: String) { products(query: $q, first: $first, after: $after) { %s } }" % FIELDS
Q_COLL = "query($id: ID!, $first: Int!, $after: String) { collection(id: $id) { products(first: $first, after: $after) { %s } } }" % FIELDS

def gql(query, variables):
    req = urllib.request.Request("%s/admin/api/%s/graphql.json" % (BASE, VER), data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Content-Type": "application/json", "X-Shopify-Access-Token": TOKEN})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r: data = json.load(r)
            if "errors" in data: raise RuntimeError(data["errors"])
            return data["data"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4: time.sleep(2 + attempt * 2); continue
            raise

nodes, after = [], None
while True:
    if COLL:
        conn = gql(Q_COLL, {"id": "gid://shopify/Collection/%s" % COLL, "first": 50, "after": after})["collection"]["products"]
    else:
        conn = gql(Q_SEARCH, {"q": SEARCH, "first": 50, "after": after})["products"]
    nodes += [e["node"] for e in conn["edges"]]
    if not conn["pageInfo"]["hasNextPage"]: break
    after = conn["pageInfo"]["endCursor"]
print("fetched %d products" % len(nodes))
if len(nodes) < 50:
    print("Too few products returned; refusing to rebuild from a suspicious pull."); sys.exit(4)

raw = os.path.join(ROOT, "tools", "raw-products.json")
json.dump(nodes, open(raw, "w", encoding="utf-8"))
out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_catalog.py"), raw], capture_output=True, text=True)
print(out.stdout.strip()); os.remove(raw)
if out.returncode != 0: print(out.stderr); sys.exit(out.returncode)
if "\nunchanged" in "\n" + out.stdout or out.stdout.startswith("unchanged"): sys.exit(0)
subprocess.run([sys.executable, os.path.join(ROOT, "build.py")], check=True)
sys.exit(3)
