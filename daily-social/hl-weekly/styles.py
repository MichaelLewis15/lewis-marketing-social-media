"""Alternate looks for render_weekly.py (set "style" in the spec).

navy   the original dark navy recap (lives in render_weekly.py)
light  "Clean": warm off-white page, navy type, highlighter accents, segmented progress bar
bold   "Color block": full-bleed brand color fields that wipe in, giant numerals, kinetic titles
cards  "Cards": white cards that pop onto a navy backdrop and stack as the releases go by

Every style keeps the same timing (INTRO, ITEM, OUTRO), leaves the bottom-left corner clear for
Howie and keeps text on flat, high-contrast color (no textures behind copy).
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

R = None  # render_weekly module, injected at import time

CREAM = (247, 244, 237); SLATE = (74, 90, 115); LINE = (222, 228, 236); NAVYM = (16, 52, 104)


def _hz(L):
    """Howie's spot (centre x, centre y, radius) for the soft disc behind him."""
    return (205, 1470, 205) if L.v else (210, 850, 200)


def logo_tint(color):
    lg = R.LOGO.copy(); a = lg.getchannel("A")
    out = Image.new("RGBA", lg.size, color + (255,)); out.putalpha(a); return out


_LOGOS = {}


def paste_logo_c(im, x, y, h, color, anchor="l"):
    key = (color, h)
    if key not in _LOGOS:
        src = Image.open(os.path.join(R.ENGINE, "logo.png")).convert("RGBA") if color == "color" else logo_tint(color)
        _LOGOS[key] = src.resize((int(src.width * h / src.height), h), Image.LANCZOS)
    lg = _LOGOS[key]
    if anchor == "c": x -= lg.width // 2
    if anchor == "r": x -= lg.width
    im.alpha_composite(lg, (int(x), int(y)))


def footer(im, L, logo, site_col):
    d = ImageDraw.Draw(im); W = L.W
    paste_logo_c(im, W / 2 if L.v else L.x0, L.foot - (10 if L.v else 30), 64 if L.v else 54, logo, "c" if L.v else "l")
    if L.v: d.text((W / 2, L.foot + 78), "lewismarketingoc.com", font=R.S(600, 30), fill=site_col, anchor="mm")
    else: d.text((W - 110, L.foot - 3), "lewismarketingoc.com", font=R.S(600, 28), fill=site_col, anchor="rm")


def pill_outline(d, x, y, text, font, col, width=3):
    w = d.textlength(text, font=font); h = font.size + 22
    d.rounded_rectangle((x, y, x + w + 44, y + h), radius=h // 2, outline=col, width=width)
    d.text((x + 22, y + h / 2), text, font=font, fill=col, anchor="lm")
    return w + 44


def scene(spec, t):
    """('intro', lt) / ('item', i, lt) / ('outro', lt)"""
    n = len(spec["items"])
    if t < R.INTRO: return ("intro", 0, t)
    t2 = t - R.INTRO
    if t2 < n * R.ITEM: i = int(t2 // R.ITEM); return ("item", i, t2 - i * R.ITEM)
    return ("outro", 0, t2 - n * R.ITEM)


def fade(lt, dur):
    return R.ease(lt / 0.45) * (1 - R.ease((lt - dur + 0.35) / 0.35))


# ---------------------------------------------------------------- light ("Clean")
def light_bg(W, H):
    im = Image.new("RGBA", (W, H), CREAM + (255,))
    L = R.Layout(W, H); cx, cy, r = _hz(L)
    disc = Image.new("RGBA", (W, H)); dd = ImageDraw.Draw(disc)
    dd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=R.SKY + (46,))
    dd.ellipse((cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26), outline=R.SKY + (70,), width=3)
    im.alpha_composite(disc)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 14), fill=R.NAVY); d.rectangle((0, 0, W * 0.28, 14), fill=R.SKY); d.rectangle((W * 0.28, 0, W * 0.36, 14), fill=R.YEL)
    footer(im, L, "color", SLATE)
    return im


def light_frame(L, bg, spec, t, total):
    W, H = L.W, L.H; im = bg.copy(); n = len(spec["items"]); kind, i, lt = scene(spec, t)
    if kind == "intro":
        k = R.ease(lt / 0.6)
        def f(d):
            pill_outline(d, L.x0, L.top + (180 if L.v else 70), spec.get("eyebrow", "HIGHLEVEL THIS WEEK"), R.S(600, 32 if L.v else 28), R.NAVY)
            y = L.top + (300 if L.v else 170)
            d.text((L.x0, y), spec.get("head1", "What's new"), font=L.f_head, fill=R.NAVY)
            y2 = y + L.f_head.size * 1.08; h2 = spec.get("head2", "in HighLevel")
            hw = d.textlength(h2, font=L.f_head) * R.ease((lt - 0.5) / 0.7)
            if hw > 0: d.rectangle((L.x0 - 8, y2 + L.f_head.size * 0.55, L.x0 + hw + 8, y2 + L.f_head.size * 1.02), fill=R.YEL)
            d.text((L.x0, y2), h2, font=L.f_head, fill=R.BLUE)
            d.text((L.x0, y + L.f_head.size * 2.35), spec["week"], font=L.f_why, fill=SLATE)
            d.text((L.x0, y + L.f_head.size * 2.35 + L.f_why.size * 1.6), spec.get("sub2", f"{n} updates worth knowing about"), font=L.f_why, fill=R.NAVY)
        im.alpha_composite(R.layer_text(W, H, f, k, int((1 - k) * 40)))
        return im
    if kind == "item":
        it = spec["items"][i]; a = fade(lt, R.ITEM)
        d0 = ImageDraw.Draw(im)
        # segmented progress bar
        gap = 14; seg = ((L.x1 - L.x0) - gap * (n - 1)) / n; py = L.top + (20 if L.v else -50)
        for j in range(n):
            x = L.x0 + j * (seg + gap)
            d0.rounded_rectangle((x, py, x + seg, py + 10), radius=5, fill=LINE)
            p = 1 if j < i else (min(1, lt / (R.ITEM - 0.3)) if j == i else 0)
            if p > 0: d0.rounded_rectangle((x, py, x + max(10, seg * p), py + 10), radius=5, fill=R.SKY)
        def f(d):
            y = L.top + (120 if L.v else 30)
            num = f"{i + 1:02d}"; d.text((L.x0, y), num, font=L.f_num, fill=R.BLUE)
            tag = (it.get("tag") or "New").upper(); nx = L.x0 + d.textlength(num, font=L.f_num) + 30
            R.pill(d, nx, y + L.f_num.size * 0.38, tag, R.S(600, 30 if L.v else 26), R.YEL if tag == "NEW" else R.NAVY, R.NAVY if tag == "NEW" else R.WHITE)
            d.text((L.x1, y + L.f_num.size * 0.5), f"{i + 1} of {n}", font=L.f_small, fill=SLATE, anchor="rm")
            y += L.f_num.size * 1.12
            lines = R.wrap(d, it["title"], L.f_title, L.x1 - L.x0)[:4]
            for ln in lines:
                d.text((L.x0, y), ln, font=L.f_title, fill=R.NAVY); y += L.f_title.size * 1.12
            y += 34; y0 = y
            for ln in R.wrap(d, it["why"], L.f_why, L.x1 - L.x0 - 40)[:5 if L.v else 3]:
                d.text((L.x0 + 40, y), ln, font=L.f_why, fill=SLATE); y += L.f_why.size * 1.45
            d.rectangle((L.x0, y0 + 6, L.x0 + 8, y - L.f_why.size * 0.45), fill=R.YEL)
        im.alpha_composite(R.layer_text(W, H, f, a, int((1 - R.ease(lt / 0.45)) * 50)))
        return im
    a = R.ease(lt / 0.5)
    def f(d):
        y = L.top + (100 if L.v else 120)
        for ln in R.wrap(d, spec.get("cta") or "Want these set up in your account?", L.f_head, L.x1 - L.x0):
            d.text((L.x0, y), ln, font=L.f_head, fill=R.NAVY); y += L.f_head.size * 1.1
        y += 30
        for ln in R.wrap(d, spec.get("cta2", "We'll handle the setup."), L.f_title, L.x1 - L.x0): d.text((L.x0, y), ln, font=L.f_title, fill=R.BLUE); y += L.f_title.size * 1.15
        y += L.f_title.size * 0.45
        R.pill(d, L.x0, y, spec.get("button", "Book a call: lewismarketingoc.com"), R.S(600, 40 if L.v else 34), R.NAVY, R.WHITE)
    im.alpha_composite(R.layer_text(W, H, f, a, int((1 - a) * 40)))
    return im


def light_gbp(spec, out):
    W, H = 1200, 900; im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 14), fill=R.NAVY); d.rectangle((0, 0, W * 0.28, 14), fill=R.SKY); d.rectangle((W * 0.28, 0, W * 0.36, 14), fill=R.YEL)
    d.ellipse((W - 330, H - 470, W - 30, H - 170), fill=(214, 233, 245))
    pill_outline(d, 70, 60, spec.get("eyebrow", "HIGHLEVEL THIS WEEK"), R.S(600, 26), R.NAVY)
    d.text((70, 125), spec.get("gbpTitle", "What's new in HighLevel"), font=R.O(800, 64), fill=R.NAVY)
    d.text((70, 205), spec["week"], font=R.S(400, 30), fill=SLATE)
    _gbp_list(d, spec, R.BLUE, R.NAVY)
    _gbp_howie(im)
    paste_logo_c(im, 70, H - 95, 54, "color")
    d.text((W - 60, H - 68), "lewismarketingoc.com", font=R.S(600, 26), fill=SLATE, anchor="rm")
    im.convert("RGB").save(out, quality=95)


def _gbp_list(d, spec, ncol, tcol, x=70, y=280, width=650):
    for i, it in enumerate(spec["items"]):
        d.text((x, y), f"{i + 1:02d}", font=R.O(800, 44), fill=ncol)
        ln = R.wrap(d, it["title"], R.O(700, 34), width)[:2]
        for k, l in enumerate(ln): d.text((x + 80, y + 4 + k * 40), l, font=R.O(700, 34), fill=tcol)
        y += 52 + 40 * (len(ln) - 1) + 22


def _gbp_howie(im, h=290, right=50, bottom=130):
    W, H = im.size
    howie = Image.open(os.path.join(R.TOOLS, "howie", "howie-pointL.png")).convert("RGBA")
    howie = howie.resize((int(howie.width * h / howie.height), h), Image.LANCZOS)
    im.alpha_composite(howie, (W - howie.width - right, H - howie.height - bottom))


# ---------------------------------------------------------------- bold ("Color block")
def bold_fields(n):
    cyc = [R.BLUE, R.YEL, R.NAVY]
    f = [R.NAVY] + [cyc[i % 3] for i in range(n)]
    f.append(R.BLUE if f[-1] == R.YEL else R.YEL)
    return f


def on(c):  # text colours for a field
    return (R.NAVY, NAVYM, "navy") if c == R.YEL else (R.WHITE, (214, 228, 245), "white")


def bold_bg(W, H):
    return Image.new("RGBA", (W, H), R.NAVY + (255,))


def bold_frame(L, bg, spec, t, total):
    W, H = L.W, L.H; n = len(spec["items"]); kind, i, lt = scene(spec, t)
    fields = bold_fields(n); idx = 0 if kind == "intro" else (i + 1 if kind == "item" else n + 1)
    col = fields[idx]; prev = fields[idx - 1] if idx else col
    im = Image.new("RGBA", (W, H), prev + (255,)); d = ImageDraw.Draw(im)
    # slanted wipe of the new field from the right
    p = 1 if idx == 0 else R.ease(lt / 0.55); slant = H * 0.18
    xl = W + slant - p * (W + slant * 2)
    d.polygon([(xl + slant, 0), (W + 10, 0), (W + 10, H), (xl, H)], fill=col)
    if p < 1:  # thin accent edge riding the wipe
        acc = R.YEL if col != R.YEL else R.WHITE
        d.polygon([(xl + slant - 22, 0), (xl + slant, 0), (xl, H), (xl - 22, H)], fill=acc)
    fg, fg2, logo = on(col)
    if p >= 0.98: footer(im, L, R.NAVY if logo == "navy" else R.WHITE, fg2)
    tl = lt - 0.35 if idx else lt  # text starts once the wipe has mostly landed
    if kind == "intro":
        def f(d):
            y = L.top + (60 if L.v else 10)
            d.text((L.x0, y), spec.get("eyebrow", "HIGHLEVEL THIS WEEK"), font=R.S(600, 36 if L.v else 30), fill=R.YEL); y += 90 if L.v else 70
            big = R.O(800, int(L.f_head.size * 1.2))
            for k, (txt, c) in enumerate(((spec.get("head1", "What's new"), R.WHITE), (spec.get("head2", "in HighLevel"), R.YEL))):
                kk = R.ease((tl - 0.12 * k) / 0.5); x = L.x0 - (1 - kk) * 160
                for ln in R.wrap(d, txt, big, L.x1 - L.x0):
                    d.text((x, y), ln, font=big, fill=c + (int(255 * kk),)); y += big.size * 1.04
            y += 40; d.rectangle((L.x0, y, L.x0 + 180 * R.ease((tl - 0.4) / 0.5), y + 14), fill=R.YEL); y += 60
            d.text((L.x0, y), spec["week"], font=L.f_why, fill=(214, 228, 245)); y += L.f_why.size * 1.6
            d.text((L.x0, y), spec.get("sub2", f"{n} updates worth knowing about"), font=L.f_why, fill=R.WHITE)
        im.alpha_composite(R.layer_text(W, H, f, R.ease(tl / 0.3)))
        return im
    if kind == "item":
        it = spec["items"][i]; a = 1 - R.ease((lt - R.ITEM + 0.3) / 0.3)
        # giant numeral, kept clear of the copy (bottom-right on 9:16, right column on 16:9)
        g = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(g)
        gf = R.O(800, 660 if L.v else 520); num = f"{i + 1:02d}"
        gcol = (R.NAVY + (34,)) if col == R.YEL else (R.WHITE + (30,))
        gx = W + 40 - (1 - R.ease(tl / 0.7)) * 120
        gd.text((gx, H - 60 if L.v else H - 40), num, font=gf, fill=gcol, anchor="rd")
        im.alpha_composite(g)
        x1 = L.x1 if L.v else 1250
        def f(d):
            y = L.top + (120 if L.v else 40)
            tag = (it.get("tag") or "New").upper()
            head = f"UPDATE {i + 1} OF {n}"
            d.text((L.x0, y), head, font=R.S(600, 34 if L.v else 28), fill=fg2)
            hx = L.x0 + d.textlength(head, font=R.S(600, 34 if L.v else 28)) + 26
            pill_outline(d, hx, y - 12, tag, R.S(600, 28 if L.v else 24), fg, 3)
            y += 110 if L.v else 90
            big = R.O(800, 104 if L.v else 84)
            for k, ln in enumerate(R.wrap(d, it["title"], big, x1 - L.x0)[:4]):
                kk = R.ease((tl - 0.08 * k) / 0.45)
                if kk <= 0: continue
                d.text((L.x0 - (1 - kk) * 140, y), ln, font=big, fill=fg + (int(255 * kk),)); y += big.size * 1.08
            y += 34
            d.rectangle((L.x0, y, L.x0 + 120 * R.ease((tl - 0.3) / 0.4), y + 12), fill=(R.WHITE if col == R.YEL else R.YEL) if col != R.YEL else R.NAVY)
            y += 50; ka = R.ease((tl - 0.45) / 0.4)
            for ln in R.wrap(d, it["why"], L.f_why, x1 - L.x0)[:5 if L.v else 4]:
                d.text((L.x0, y), ln, font=L.f_why, fill=fg + (int(255 * ka),)); y += L.f_why.size * 1.45
        im.alpha_composite(R.layer_text(W, H, f, a))
        return im
    def f(d):
        y = L.top + (100 if L.v else 110); big = R.O(800, int(L.f_head.size * 1.05))
        for k, ln in enumerate(R.wrap(d, spec.get("cta") or "Want these set up in your account?", big, L.x1 - L.x0)):
            kk = R.ease((tl - 0.1 * k) / 0.45)
            d.text((L.x0 - (1 - kk) * 140, y), ln, font=big, fill=fg + (int(255 * max(0, kk)),)); y += big.size * 1.08
        y += 40
        for ln in R.wrap(d, spec.get("cta2", "We'll handle the setup."), L.f_title, L.x1 - L.x0): d.text((L.x0, y), ln, font=L.f_title, fill=fg2 if col != R.YEL else R.BLUE); y += L.f_title.size * 1.15
        y += L.f_title.size * 0.45
        if tl > 0.5:
            bf = R.S(600, 40 if L.v else 34)
            R.pill(d, L.x0, y, spec.get("button", "Book a call: lewismarketingoc.com"), bf, R.NAVY if col == R.YEL else R.YEL, R.WHITE if col == R.YEL else R.NAVY)
    im.alpha_composite(R.layer_text(W, H, f, R.ease(tl / 0.3)))
    return im


def bold_gbp(spec, out):
    W, H = 1200, 900; im = Image.new("RGBA", (W, H), R.BLUE + (255,)); d = ImageDraw.Draw(im)
    d.polygon([(W * 0.72, 0), (W, 0), (W, H), (W * 0.6, H)], fill=R.NAVY)
    d.polygon([(W * 0.72 - 18, 0), (W * 0.72, 0), (W * 0.6, H), (W * 0.6 - 18, H)], fill=R.YEL)
    d.text((70, 62), spec.get("eyebrow", "HIGHLEVEL THIS WEEK"), font=R.S(600, 28), fill=R.YEL)
    y = 110
    for ln in R.wrap(d, spec.get("gbpTitle", "What's new in HighLevel"), R.O(800, 64), 620):
        d.text((70, y), ln, font=R.O(800, 64), fill=R.WHITE); y += 70
    d.text((70, y + 10), spec["week"], font=R.S(400, 30), fill=(214, 228, 245))
    _gbp_list(d, spec, R.YEL, R.WHITE, y=y + 80, width=560)
    _gbp_howie(im, right=40)
    paste_logo_c(im, 70, H - 95, 54, R.WHITE)
    d.text((W - 60, H - 68), "lewismarketingoc.com", font=R.S(600, 26), fill=R.WHITE, anchor="rm")
    im.convert("RGB").save(out, quality=95)


# ---------------------------------------------------------------- cards ("Cards")
def cards_bg(W, H):
    y = np.linspace(0, 1, H)[:, None, None]
    img = np.array(R.NAVY, float) * (1 - y) + np.array(R.NAVY2, float) * y
    im = Image.fromarray(np.broadcast_to(img, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    glow = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(glow)
    gd.ellipse((W * 0.25, -H * 0.2, W * 1.05, H * 0.35), fill=R.SKY + (55,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W // 8)))
    L = R.Layout(W, H); footer(im, L, R.WHITE, R.MIST)
    return im


_CARD = {}


def card_box(L):
    return (60, 340, L.W - 60) if L.v else (440, 100, L.W - 90)  # x0, top, x1


def make_card(L, key, draw_fn, hmax):
    """render a white card (with shadow) once; draw_fn(d, x, y, w) -> used height."""
    if (L.W, key) in _CARD: return _CARD[(L.W, key)]
    cx0, top, cx1 = card_box(L); w = cx1 - cx0; pad = 64 if L.v else 56
    probe = Image.new("RGBA", (w, 4000)); h = draw_fn(ImageDraw.Draw(probe), pad, pad, w - pad * 2) + pad * 2 - 20
    h = int(min(h, hmax))
    m = 60; img = Image.new("RGBA", (w + m * 2, h + m * 2))
    sh = Image.new("RGBA", img.size); ImageDraw.Draw(sh).rounded_rectangle((m, m + 18, m + w, m + h + 18), radius=40, fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    d = ImageDraw.Draw(img); d.rounded_rectangle((m, m, m + w, m + h), radius=40, fill=R.WHITE)
    draw_fn(d, m + pad, m + pad, w - pad * 2)
    if not L.v: top = max(90, int((900 - h) / 2 - 20))
    _CARD[(L.W, key)] = (img, m, h, top); return _CARD[(L.W, key)]


def put_card(im, L, card, a, dy=0, scale=1.0):
    img, m, h, top = card; cx0 = card_box(L)[0]
    if scale != 1.0:
        nw, nh = int(img.width * scale), int(img.height * scale)
        img = img.resize((nw, nh), Image.BILINEAR); ox = (card[0].width - nw) / 2; oy = (card[0].height - nh) / 2
    else: ox = oy = 0
    if a < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    im.alpha_composite(img, (int(cx0 - m + ox), int(top - m + oy + dy)))


def _item_card(d, x, y, w, L, it, i, n):
    y0 = y; r = 52 if L.v else 44
    d.ellipse((x, y, x + r * 2, y + r * 2), fill=R.SKY)
    d.text((x + r, y + r), str(i + 1), font=R.O(800, 60 if L.v else 50), fill=R.WHITE, anchor="mm")
    tag = (it.get("tag") or "New").upper()
    R.pill(d, x + r * 2 + 24, y + r - (28 if L.v else 24), tag, R.S(600, 28 if L.v else 24), R.YEL if tag == "NEW" else R.NAVY, R.NAVY if tag == "NEW" else R.WHITE)
    d.text((x + w, y + r), f"{i + 1} of {n}", font=L.f_small, fill=SLATE, anchor="rm")
    y += r * 2 + (44 if L.v else 34)
    for ln in R.wrap(d, it["title"], L.f_title, w)[:4]:
        d.text((x, y), ln, font=L.f_title, fill=R.NAVY); y += L.f_title.size * 1.1
    y += 26; d.line((x, y, x + w, y), fill=LINE, width=3); y += 36
    for ln in R.wrap(d, it["why"], L.f_why, w)[:5 if L.v else 3]:
        d.text((x, y), ln, font=L.f_why, fill=SLATE); y += L.f_why.size * 1.45
    return y - y0


def cards_frame(L, bg, spec, t, total):
    W, H = L.W, L.H; im = bg.copy(); n = len(spec["items"]); kind, i, lt = scene(spec, t)
    hmax = (1230 - 300) if L.v else (900 - 100)
    if kind == "intro":
        def draw(d, x, y, w):
            y0 = y
            R.pill(d, x, y, spec.get("eyebrow", "HIGHLEVEL THIS WEEK"), R.S(600, 30 if L.v else 26), R.SKY, R.WHITE); y += 100 if L.v else 84
            for txt, c in ((spec.get("head1", "What's new"), R.NAVY), (spec.get("head2", "in HighLevel"), R.BLUE)):
                for ln in R.wrap(d, txt, L.f_head, w): d.text((x, y), ln, font=L.f_head, fill=c); y += L.f_head.size * 1.06
            y += 30; d.rectangle((x, y, x + 110, y + 10), fill=R.YEL); y += 50
            d.text((x, y), spec["week"], font=L.f_why, fill=SLATE); y += L.f_why.size * 1.55
            for ln in R.wrap(d, spec.get("sub2", f"{n} updates worth knowing about"), L.f_why, w):
                d.text((x, y), ln, font=L.f_why, fill=R.NAVY); y += L.f_why.size * 1.4
            return y - y0
        k = R.ease(lt / 0.55)
        put_card(im, L, make_card(L, ("intro", spec["week"]), draw, hmax), k, (1 - k) * 120, 0.94 + 0.06 * k)
        return im
    if kind == "item":
        it = spec["items"][i]
        def draw(d, x, y, w):
            return _item_card(d, x, y, w, L, it, i, n)
        card = make_card(L, ("item", i, it["title"]), draw, hmax)
        # stack of finished cards peeking above
        cx0, _, cx1 = card_box(L); top = card[3]; d0 = ImageDraw.Draw(im)
        for k in range(min(i, 2), 0, -1):
            inset = 36 * k; yy = top - 34 * k
            d0.rounded_rectangle((cx0 + inset, yy, cx1 - inset, yy + 200), radius=36, fill=(200, 212, 228) if k == 2 else (226, 233, 242))
        kin = R.ease(lt / 0.5); kout = R.ease((lt - R.ITEM + 0.4) / 0.4)
        put_card(im, L, card, kin * (1 - kout), (1 - kin) * 160 - kout * 90, (0.92 + 0.08 * kin) * (1 - 0.06 * kout))
        # progress pips under the card
        dd = ImageDraw.Draw(im); py = (1300 if L.v else 940); px = (W / 2 - (n - 1) * 22) if L.v else (W - 110 - (n - 1) * 44 - 400)
        if L.v:
            for j in range(n):
                cx = px + j * 44; dd.rounded_rectangle((cx - (22 if j == i else 9), py - 9, cx + (22 if j == i else 9), py + 9), radius=9, fill=R.YEL if j == i else (255, 255, 255, 70))
        return im
    def draw(d, x, y, w):
        y0 = y
        for ln in R.wrap(d, spec.get("cta") or "Want these set up in your account?", L.f_head, w):
            d.text((x, y), ln, font=L.f_head, fill=R.NAVY); y += L.f_head.size * 1.08
        y += 26
        for ln in R.wrap(d, spec.get("cta2", "We'll handle the setup."), L.f_title, w): d.text((x, y), ln, font=L.f_title, fill=R.BLUE); y += L.f_title.size * 1.12
        y += L.f_title.size * 0.45
        R.pill(d, x, y, spec.get("button", "Book a call: lewismarketingoc.com"), R.S(600, 38 if L.v else 32), R.NAVY, R.WHITE)
        return y + 80 - y0
    k = R.ease(lt / 0.55)
    put_card(im, L, make_card(L, ("outro", spec.get("cta")), draw, hmax), k, (1 - k) * 120, 0.94 + 0.06 * k)
    return im


def cards_gbp(spec, out):
    W, H = 1200, 900
    im = Image.new("RGBA", (W, H)); im.alpha_composite(_cards_plain(W, H))
    d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", (W, H)); ImageDraw.Draw(sh).rounded_rectangle((50, 68, 830, 778), radius=36, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    d.rounded_rectangle((50, 50, 830, 760), radius=36, fill=R.WHITE)
    R.pill(d, 100, 95, spec.get("eyebrow", "HIGHLEVEL THIS WEEK"), R.S(600, 24), R.SKY, R.WHITE)
    y = 160
    for ln in R.wrap(d, spec.get("gbpTitle", "What's new in HighLevel"), R.O(800, 50), 690):
        d.text((100, y), ln, font=R.O(800, 50), fill=R.NAVY); y += 58
    d.text((100, y + 8), spec["week"], font=R.S(400, 28), fill=SLATE); y += 70
    d.line((100, y, 780, y), fill=LINE, width=3); y += 26
    for i, it in enumerate(spec["items"]):
        d.ellipse((100, y, 148, y + 48), fill=R.SKY); d.text((124, y + 24), str(i + 1), font=R.O(800, 28), fill=R.WHITE, anchor="mm")
        ln = R.wrap(d, it["title"], R.O(700, 30), 600)[:2]
        for k, l in enumerate(ln): d.text((170, y + 6 + k * 36), l, font=R.O(700, 30), fill=R.NAVY)
        y += 48 + 36 * (len(ln) - 1) + 20
    _gbp_howie(im, h=300, right=30, bottom=120)
    paste_logo_c(im, 60, H - 92, 50, R.WHITE)
    d.text((W - 60, H - 66), "lewismarketingoc.com", font=R.S(600, 26), fill=R.MIST, anchor="rm")
    im.convert("RGB").save(out, quality=95)


def _cards_plain(W, H):
    y = np.linspace(0, 1, H)[:, None, None]
    img = np.array(R.NAVY, float) * (1 - y) + np.array(R.NAVY2, float) * y
    im = Image.fromarray(np.broadcast_to(img, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    glow = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(glow)
    gd.ellipse((W * 0.5, -H * 0.2, W * 1.1, H * 0.4), fill=R.SKY + (55,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W // 8)))
    return im


STYLES = {
    "light": dict(bg=light_bg, frame=light_frame, gbp=light_gbp, label="Clean"),
    "bold": dict(bg=bold_bg, frame=bold_frame, gbp=bold_gbp, label="Color block"),
    "cards": dict(bg=cards_bg, frame=cards_frame, gbp=cards_gbp, label="Cards"),
}
