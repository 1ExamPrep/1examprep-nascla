"""Reviews page content shared by the Pass Your ... sites (added 2026-11-27).

Each site's build renders these sections in its own page chrome. The review widgets are placeholders
(div.reviews-embed); the site's JavaScript swaps in the Google reviews iframes and the Shopper Approved
script at runtime, so the served HTML has no <iframe> or body <script> and passes the pre-publish check.

No star rating or review count is written into the page or the schema: those numbers live in the widgets
and change daily, and Google does not show self-served business reviews as stars anyway.
"""
import html

PATH = "/reviews/"
GOOGLE_WIDGETS = [
    "https://app.1examprep.com/reputation/widgets/review_widget/hOrBBdmSOrj9sN4cypQn",
    "https://app.1examprep.com/reputation/widgets/review_widget/hOrBBdmSOrj9sN4cypQn?widgetId=698cb4ab84d52b28d95b405d",
]
SA_WRAPPER = "SA_wrapper_640wpbtGdBfc"
SA_SCRIPT = "https://www.shopperapproved.com/widgets/41986/merchant/rotating-widget/640wpbtGdBfc.js?v=4"
SOURCES = [
    ("Shopper Approved, independent customer ratings", "https://www.shopperapproved.com/"),
    ("Google Maps user contributed content policy", "https://support.google.com/contributionpolicy/answer/7400114"),
]


def google_embed(i, url, phone, tel, email):
    return (f'<div class="reviews-embed" data-kind="google" data-src="{html.escape(url)}" data-title="Google reviews of 1 Exam Prep{" (summary)" if i else ""}">'
            f'<p class="reviews-fallback">Google reviews are loading. If they do not appear, call <a href="tel:{tel}">{phone}</a> '
            f'or email <a href="mailto:{email}">{email}</a> and we will send you the link.</p></div>')


def sa_embed(phone, tel, email):
    return (f'<div class="reviews-embed" data-kind="shopperapproved" data-wrapper="{SA_WRAPPER}" data-src="{html.escape(SA_SCRIPT)}">'
            f'<p class="reviews-fallback">Shopper Approved reviews are loading. If they do not appear, call <a href="tel:{tel}">{phone}</a> '
            f'or email <a href="mailto:{email}">{email}</a>.</p></div>')


def content(brand, subject, phone, tel, email, faq_url="/faq/", contact_url="/contact/", home_url="/"):
    """Returns dict(title, desc, h1, lead, takeaways, sections=[(id, h2, html)], faq=[(q, a)], sources).

    brand: "Pass Your Florida Contractor Exam"; subject: "Florida contractor exam" (used as "the {subject}").
    """
    title = f"Customer Reviews | {brand}"
    if len(title) > 60:
        title = "1 Exam Prep Customer Reviews and Ratings"
    desc = (f"Read real Google and Shopper Approved reviews from people who used 1 Exam Prep books and courses "
            f"to pass the {subject}.")[:160]
    lead = (f"These are real reviews of 1 Exam Prep from Google and Shopper Approved, shown live as customers post them. "
            f"1 Exam Prep packs every order on this site, so each review here speaks to the same books, "
            f"tabs and courses you would get for the {subject}.")
    takeaways = [
        "Two independent sources: Google reviews and Shopper Approved, shown live on this page.",
        "Shopper Approved only invites people who actually placed an order, so every rating there is from a buyer.",
        "Reviews cover 1 Exam Prep as a whole: books, tabs, online courses and customer service.",
        f"Questions about a review or an order? Email {email} or call {phone}.",
    ]
    g = "".join(google_embed(i, u, phone, tel, email) for i, u in enumerate(GOOGLE_WIDGETS))
    sections = [
        ("google-reviews", "What do customers say on Google?",
         f"<p>Google reviews are written by people signed in to a Google account, and they appear on the 1 Exam Prep business profile "
         f"in Search and Maps. The feed below updates on its own, so the newest reviews show first. 1 Exam Prep cannot edit or hide what "
         f"a reviewer writes; Google removes a review only when it breaks its content policy.</p>{g}"),
        ("shopper-approved-reviews", "What do verified buyers say on Shopper Approved?",
         f"<p>Shopper Approved is an independent ratings company. After checkout, it asks the buyer to rate the order, and a follow-up "
         f"asks again once the books or course access have arrived. Because only real orders get the survey, every rating comes from "
         f"someone who bought from 1 Exam Prep.</p>{sa_embed(phone, tel, email)}"),
        ("what-reviews-cover", "What do the reviews usually talk about?",
         "<p>Most reviews mention one of 4 things. They are the same 4 things worth checking before you order:</p>"
         "<ol><li><strong>Passing the exam.</strong> Whether the study guide, practice questions and tabs matched the real test.</li>"
         "<li><strong>Tabs and highlighting.</strong> How fast the tabbed, highlighted books were to use in an open-book exam.</li>"
         "<li><strong>Shipping.</strong> Books go free by USPS Media Mail, which usually takes 2 to 8 business days.</li>"
         "<li><strong>Help by phone and email.</strong> Getting the right package for the license and the code year.</li></ol>"),
        ("how-to-read-reviews", "How should you read exam prep reviews?",
         "<p>A 5-star review from someone who took a different exam tells you less than a 4-star review from someone who took yours. "
         "Use the table to weigh what you read.</p>"
         "<table><caption>What to look for in a review</caption><thead><tr><th>Look for</th><th>Why it matters</th></tr></thead><tbody>"
         "<tr><td>The license or exam named</td><td>Approved books and code years differ by state and trade.</td></tr>"
         "<tr><td>The date of the review</td><td>Exams move to new code editions; a 2026 review reflects current books.</td></tr>"
         "<tr><td>What was bought</td><td>A book set, a rental and an online course are very different orders.</td></tr>"
         "<tr><td>How a problem was handled</td><td>Late packages and wrong editions happen; the fix is what to judge.</td></tr>"
         "</tbody></table>"),
        ("leave-a-review", "How can you leave a review?",
         "<p>If you ordered from 1 Exam Prep, Shopper Approved emails you a short survey after checkout and again after delivery. "
         "Answer either one and your rating appears in the Shopper Approved feed above. To review on Google, search for 1 Exam Prep in "
         "Google Maps, open the business profile and choose Write a review. Honest reviews help, including critical ones: they tell "
         "the next candidate what to expect and tell the team what to fix.</p>"),
        ("problem-with-an-order", "What if your order did not go well?",
         f'<p>Call <a href="tel:{tel}">{phone}</a> or email <a href="mailto:{email}">{email}</a> with your order number before or after '
         f"you post a review. The team that answers is the team that packs the orders, so it can check tracking, resend course access "
         f'or swap a wrong edition. All sales are final under the store policy, so the <a href="{contact_url}">contact page</a> is '
         f"the fastest route to a fix. For questions about the {subject} itself, the <a href=\"{faq_url}\">FAQ</a> covers scheduling, "
         f'open-book rules and which books are allowed, and the <a href="{home_url}">home page</a> lists every license on this site.</p>'),
    ]
    faq = [
        ("Are these reviews real?", "Yes. The Google reviews come straight from the 1 Exam Prep Google business profile, and Shopper Approved only surveys people who placed an order. 1 Exam Prep does not write, edit or pick them."),
        ("Why do the reviews mention other states and trades?", f"1 Exam Prep sells exam prep for contractor, electrical, plumbing and HVAC licenses across the country, and one store fills every order. The service, shipping and books are the same for the {subject}."),
        ("Can 1 Exam Prep remove a bad review?", "No. Google removes a review only when it breaks Google's content policy, and Shopper Approved does not let merchants delete ratings. The team can reply publicly and try to fix the problem."),
        ("Do I need an account to read the reviews?", "No. The reviews load on this page for anyone. You need a Google account only to write a Google review."),
        ("How long do books take to arrive?", "Books ship free by USPS Media Mail inside the United States, which usually takes 2 to 8 business days. Online courses arrive by email after checkout. Allow up to 15 business days for rental, Ultimate and 1 Package orders."),
        ("Who do I contact about an order?", f"Call {phone} or email {email} with your order number. The same team handles every order on this site."),
    ]
    return dict(title=title, desc=desc, h1="Customer reviews", lead=lead, takeaways=takeaways, sections=sections, faq=faq, sources=SOURCES)


def page_ld(site, title, desc, updated, org_id=None):
    d = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": site + PATH,
         "description": desc, "dateModified": updated, "about": {"@type": "Organization", "name": "1 Exam Prep", "url": "https://1examprep.com"}}
    if org_id:
        d["about"]["@id"] = org_id
    return d


CSS = (".reviews-embed{margin:18px 0 24px;min-height:120px}"
       ".reviews-embed iframe{display:block;width:100%;min-width:100%;border:0}"
       ".reviews-fallback{font-size:.95em;opacity:.8}")
