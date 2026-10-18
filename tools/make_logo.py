"""Cut the site's logo assets from brand/logo-source.png (transparent PNG of the full logo).
Run once after replacing the source:  python3 tools/make_logo.py
Writes shared/logo-full.png, logo-nav.png (header, 2x), logo-mark.png (square icon), favicon.png, apple-touch-icon.png, logo.png (1200x630 social card)."""
import os, sys
from PIL import Image, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = Image.open(os.path.join(ROOT, "brand", "logo-source.png")).convert("RGBA")
# clean stray semi-transparent speckles, then trim
a = src.getchannel("A").point(lambda v: 255 if v > 140 else 0)
src.putalpha(a)
full = src.crop(src.getbbox())
out = os.path.join(ROOT, "shared")
full.save(os.path.join(out, "logo-full.png"), optimize=True)
# header version: 2x for retina, 96px tall
nav = full.resize((round(full.width * 96 / full.height), 96), Image.LANCZOS); nav.save(os.path.join(out, "logo-nav.png"), optimize=True)
# the mark: everything left of the wordmark (largest gap of empty columns splits icon from text)
cols = [x for x in range(full.width) if full.crop((x, 0, x + 1, full.height)).getbbox()]
gaps, start = [], cols[0]
for p, n in zip(cols, cols[1:]):
    if n - p > 12: gaps.append((n - p, p, n))
split = max(gaps)[1] if gaps else full.width // 3
mark = full.crop((0, 0, split + 1, full.height)); mark = mark.crop(mark.getbbox())
side = max(mark.size) + 40; sq = Image.new("RGBA", (side, side), (0, 0, 0, 0)); sq.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2), mark)
sq.resize((512, 512), Image.LANCZOS).save(os.path.join(out, "logo-mark.png"), optimize=True)
# favicon (navy rounded square behind the mark so it reads on any tab colour) + apple touch icon
def tile(size, pad):
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0)); from PIL import ImageDraw
    ImageDraw.Draw(bg).rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=(247, 246, 242, 255))
    m = sq.resize((size - 2 * pad, size - 2 * pad), Image.LANCZOS); bg.paste(m, (pad, pad), m); return bg
tile(64, 6).save(os.path.join(out, "favicon.png"), optimize=True)
tile(180, 16).convert("RGB").save(os.path.join(out, "apple-touch-icon.png"), optimize=True)
# social card 1200x630 on the site background
card = Image.new("RGB", (1200, 630), (247, 246, 242)); w = 1000; h = round(full.height * w / full.width)
if h > 420: h = 420; w = round(full.width * h / full.height)
lg = full.resize((w, h), Image.LANCZOS); card.paste(lg, ((1200 - w) // 2, (630 - h) // 2), lg); card.save(os.path.join(out, "logo.png"), optimize=True)
print("logo-full", full.size, "mark split at", split, "nav", nav.size)
