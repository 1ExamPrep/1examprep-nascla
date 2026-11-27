"""Product structured data (schema.org JSON-LD) shared by the Pass Your ... sites.

The same file lives in tools/ of every site repo (Texas, Virginia, Electrician, Nevada, HVAC, Plumbing,
Mississippi, NASCLA), so they all describe
products the same way. build.py calls product_ld() (or delivery_fields() for its own offers) on every product page.

Store facts below come from the 1 Exam Prep Shopify store (1examprep.com), checked 2026-10-28:
  - Shipping: the only delivery method is "Free USPS (Media Mail)", United States only.
  - Returns: the refund policy says "All sales are final"; returns only with supervisor approval and a 20%
    restocking fee. In schema.org terms that is MerchantReturnNotPermitted.
  - Delivery time (added 2026-11-27): books 0-2 handling + 2-8 transit business days; rental, Ultimate and
    1 Package orders 0-7 handling + 2-8 transit (up to 15); online access 0-1 handling, no transit.
Re-check them when the store's shipping profile or refund policy changes, then rebuild.
"""
import re

STORE_SELLER = {"@type": "Organization", "name": "1 Exam Prep", "url": "https://1examprep.com"}
RETURN_POLICY_URL = "https://1examprep.com/policies/refund-policy"

RETURN_POLICY = {
    "@type": "MerchantReturnPolicy",
    "applicableCountry": "US",
    "returnPolicyCategory": "https://schema.org/MerchantReturnNotPermitted",
    "merchantReturnLink": RETURN_POLICY_URL,
}
# deliveryTime (Google Search Console "Missing field deliveryTime", November 27, 2026).
# Numbers match what the sites already tell buyers: USPS Media Mail "usually takes 2 to 8 business days",
# and "allow up to 15 business days for rental, Ultimate and 1 Package orders" (up to 7 days to pack + 8 in transit).
# Online access goes out by email the same or next business day with no transit.
BUSINESS_DAYS = {"@type": "OpeningHoursSpecification",
                 "dayOfWeek": ["https://schema.org/Monday", "https://schema.org/Tuesday", "https://schema.org/Wednesday",
                               "https://schema.org/Thursday", "https://schema.org/Friday"]}


def delivery_time(handling_min, handling_max, transit_min, transit_max):
    """schema.org ShippingDeliveryTime in business days."""
    return {"@type": "ShippingDeliveryTime", "businessDays": BUSINESS_DAYS,
            "handlingTime": {"@type": "QuantitativeValue", "minValue": handling_min, "maxValue": handling_max, "unitCode": "DAY"},
            "transitTime": {"@type": "QuantitativeValue", "minValue": transit_min, "maxValue": transit_max, "unitCode": "DAY"}}


BOOK_DELIVERY_TIME = delivery_time(0, 2, 2, 8)
LONG_DELIVERY_TIME = delivery_time(0, 7, 2, 8)
EMAIL_DELIVERY_TIME = delivery_time(0, 1, 0, 0)

FREE_US_SHIPPING = {
    "@type": "OfferShippingDetails",
    "shippingLabel": "Free USPS Media Mail",
    "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "USD"},
    "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "US"},
    "deliveryTime": BOOK_DELIVERY_TIME,
}
# Rental, Ultimate and 1 Package orders: same free Media Mail, longer to put together.
FREE_US_SHIPPING_LONG = dict(FREE_US_SHIPPING, deliveryTime=LONG_DELIVERY_TIME)
# Online courses and services ship nothing: access arrives by email, so delivery is free.
# Google still wants shippingDetails on every offer, so these get a $0 email delivery instead of no entry.
EMAIL_DELIVERY = {
    "@type": "OfferShippingDetails",
    "shippingLabel": "Online access by email, nothing shipped",
    "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "USD"},
    "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "US"},
    "deliveryTime": EMAIL_DELIVERY_TIME,
}
LONG_ORDER = re.compile(r"\b(rental|ultimate|1 package)\b", re.I)

# Product types and title words that mean nothing is shipped (access arrives by email).
DIGITAL_TYPES = {"online course", "practice course", "application", "live training", "continuing education"}
DIGITAL_TITLE = re.compile(r"\b(online (exam prep|course|practice)|test success kit|webinar|filing|formation setup|application service|licensing tests)\b", re.I)
BOOK_TITLE = re.compile(r"\b(book|books|study guide|code book|tabs|flash cards?|rental|package|combo|kit)\b", re.I)
RENTAL = re.compile(r"\brental\b", re.I)


def ships(title, ptype):
    """True when the order includes something physical (books, tabs, flash cards)."""
    t = (ptype or "").strip().lower()
    if t in DIGITAL_TYPES:
        return False
    if DIGITAL_TITLE.search(title or "") and not re.search(r"\b(books?|study guides?|code book|flash cards|tabs)\b", title or "", re.I):
        return False
    return True


def condition(title, ptype):
    """Only physical items sold new get a condition. Rentals and online access get none."""
    if not ships(title, ptype) or RENTAL.search(title or "") or "rental" in (ptype or "").lower() or (ptype or "").lower() == "ultimate package":
        return None
    return "https://schema.org/NewCondition"


def clean_description(text, limit=500):
    """Whole sentences up to about `limit` characters. Returns "" when the text has no complete sentence
    (for example a description that was cut off when it was pulled), so the caller can use a fallback."""
    t = re.sub(r"\s+", " ", text or "").strip()
    t = re.sub(r"(\.\.\.|\u2026)\s*$", "", t).strip()
    window = t[:limit + 1]
    ends = [m.end() for m in re.finditer(r"[.!?][\"')\]]?(?=\s|$)", window)]
    ends = [e for e in ends if e >= 20]
    if not ends:
        return ""
    return window[:ends[-1]].strip()


def delivery_fields(title, ptype=""):
    """shippingDetails and hasMerchantReturnPolicy for one offer. Every offer gets both (Google flags either one missing)."""
    if not ships(title, ptype):
        shipping = EMAIL_DELIVERY
    elif LONG_ORDER.search(title or "") or LONG_ORDER.search(ptype or ""):
        shipping = FREE_US_SHIPPING_LONG
    else:
        shipping = FREE_US_SHIPPING
    return {"shippingDetails": shipping, "hasMerchantReturnPolicy": RETURN_POLICY}


def offer(v, product_name, url, ptype):
    name = v.get("title") or ""
    o = {"@type": "Offer"}
    if name and name != "Default Title":
        o["name"] = name
    else:
        o["name"] = product_name
    o.update({"priceCurrency": "USD", "price": "%.2f" % float(v["price"]),
              "availability": "https://schema.org/InStock" if v.get("available", True) else "https://schema.org/OutOfStock",
              "url": url, "seller": STORE_SELLER})
    cond = condition(product_name + " " + name, ptype)
    if cond:
        o["itemCondition"] = cond
    o.update(delivery_fields(product_name + " " + name, ptype))
    return o


def product_ld(name, url, images, description, sku, category, variants, ptype, brand="1 Exam Prep", fallback=""):
    """A complete schema.org Product for one product page. `fallback` is used when the description has no full sentence."""
    images = [i for i in images if i][:6]
    d = {"@context": "https://schema.org", "@type": "Product", "@id": url + "#product", "name": name, "url": url,
         "mainEntityOfPage": url, "image": images, "description": clean_description(description) or clean_description(fallback) or name,
         "brand": {"@type": "Brand", "name": brand}, "sku": str(sku), "productID": str(sku), "category": category,
         "offers": [offer(v, name, url, ptype) for v in variants]}
    return d
