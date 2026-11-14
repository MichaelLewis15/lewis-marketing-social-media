"""Lewis Marketing video engine (formats x styles x sizes, optional Howie, voiceover and captions).

Entry point: render_weekly.py (python3 render_weekly.py spec.json OUTDIR, or --preview spec.json OUTDIR).

FORMATS ("format" in the spec, default "list")
  list        recap of 3-5 points: items[{title, why, tag}]                       (HighLevel Weekly, launches, tips)
  myth        myth vs fact: items[{myth, fact}] (1-4)
  beforeafter before[{title, points[]}] and after{title, points[]}
  stat        stats[{value, label, source, url}] (1-4); every stat needs a credible source (shown on screen)
  results     monthly results recap: month, stats[{value, label}] combined across clients, never naming a client
  review      reviews[{text, name, stars, source}] (1-3); real reviews only, first name + last initial
  podcast     episode{show, number, title, guest, quote}; optional "audio": clip.wav/mp3 (used as the soundtrack, drives the waveform)
  countdown   event{name, date "YYYY-MM-DD", time, place}; "postDate" (YYYY-MM-DD, the day it posts) sets the day count
Shared keys: eyebrow, head1, head2, week (subtitle line), sub2, cta, cta2, button, gbpTitle, music 0-3.

STYLES ("style"): navy | light | bold | cards (normal rotation) and seasonal holiday | shopsmall | yearend
SIZES ("sizes", default all): 916 (1080x1920), 169 (1920x1080), 45 (1080x1350 feed), 11 (1080x1080 square)
"howie": false leaves Howie out.  "voice": true adds a narrated voiceover (voice.py), "captions" (default = voice) burns in captions.
"voiceName": Kokoro voice (default af_heart).  Scene narration defaults to the on-screen words; override with "vo" on an item
or spec["vo"] = {"intro": "...", "outro": "..."}.
Outputs: v916.mp4 v169.mp4 v45.mp4 v11.mp4 (as requested), cover<size>.jpg, gbp.png, voice-check.json when voiced.
"""
import json, os, re, sys, subprocess, tempfile, math, datetime, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "howie-tools")
ENGINE = os.path.join(HERE, "..", "engine")
sys.path.insert(0, TOOLS)
import music, howie_reel  # noqa: E402

FPS = 30
NAVY = (10, 31, 68); NAVY2 = (5, 16, 38); SKY = (41, 162, 222); BLUE = (4, 107, 210)
YEL = (244, 197, 66); WHITE = (255, 255, 255); MIST = (200, 214, 230)
CREAM = (247, 244, 237); SLATE = (74, 90, 115); LINE = (222, 228, 236); NAVYM = (16, 52, 104)
RED = (196, 32, 50); GOLD = (226, 186, 88); NIGHT = (7, 14, 30)
_F = {}


def O(w, s):
    k = ("o", w, int(s))
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(TOOLS, f"outfit-latin-{w}-normal.woff"), int(s))
    return _F[k]


def S(w, s):
    k = ("s", w, int(s))
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(TOOLS, f"open-sans-latin-{w}-normal.woff"), int(s))
    return _F[k]


def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def wrap(d, text, font, width):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def pill(d, x, y, text, font, fill, fg, outline=None):
    w = d.textlength(text, font=font); h = font.size + 22
    if outline: d.rounded_rectangle((x, y, x + w + 44, y + h), radius=h // 2, outline=outline, width=3)
    else: d.rounded_rectangle((x, y, x + w + 44, y + h), radius=h // 2, fill=fill)
    d.text((x + 22, y + h / 2), text, font=font, fill=fg, anchor="lm")
    return w + 44, h


def star(d, cx, cy, r, fill):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def check(d, x, y, s, col, w=None):
    d.line([(x, y + s * 0.55), (x + s * 0.38, y + s * 0.9), (x + s, y + s * 0.1)], fill=col, width=w or max(4, int(s / 6)), joint="curve")


def cross(d, x, y, s, col):
    w = max(4, int(s / 6)); d.line([(x, y), (x + s, y + s)], fill=col, width=w); d.line([(x + s, y), (x, y + s)], fill=col, width=w)


def alpha(img, a):
    if a >= 1: return img
    img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * max(0, a)))); return img


def shift(img, dx=0, dy=0):
    if not dx and not dy: return img
    return img.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy))


# ------------------------------------------------------------------ sizes
SIZES = {"916": (1080, 1920), "169": (1920, 1080), "45": (1080, 1350), "11": (1080, 1080)}
CFG = {
    "916": dict(x0=90, x1=990, top=330, bottom=1250, foot=1735, fs=(124, 88, 48, 230, 36), hz=(0, 1000, 1.0), disc=(205, 1470, 205), cap=(360, 1565, 1010, 46), logo=64, site=30, prog=270),
    "169": dict(x0=470, x1=1810, top=120, bottom=900, foot=965, fs=(100, 72, 40, 180, 30), hz=(20, 430, 1.0), disc=(210, 850, 200), cap=(470, 845, 1810, 38), logo=54, site=28, prog=70),
    "45": dict(x0=80, x1=1000, top=110, bottom=1000, foot=1240, fs=(96, 70, 38, 170, 30), hz=(0, 798, 0.72), disc=(150, 1120, 150), cap=(270, 1105, 1000, 36), logo=56, site=28, prog=55),
    "11": dict(x0=70, x1=1010, top=80, bottom=770, foot=975, fs=(84, 60, 34, 140, 28), hz=(0, 600, 0.6), disc=(125, 870, 125), cap=(225, 790, 1010, 32), logo=50, site=26, prog=38),
}


class Layout:
    def __init__(self, key, howie=True, captions=False):
        self.key = key; self.W, self.H = SIZES[key]; self.wide = key == "169"; self.v = not self.wide
        c = CFG[key]; self.__dict__.update(c); self.howie = howie; self.captions = captions
        if captions and key == "169": self.bottom = 820
        cx0, cy, cx1, cf = c["cap"]
        self.cap = (cx0 if howie else self.x0, cy, cx1, cf)

    def fonts(self, s=1.0):
        h, t, w, n, sm = self.fs
        return type("F", (), dict(head=O(800, h * s), title=O(800, t * s), why=S(400, w * s), num=O(800, n * s), small=S(600, sm * s),
                                  pill=S(600, max(22, sm * 0.85 * s)), s=s, base=self.fs))


# ------------------------------------------------------------------ palettes
def P(**k):
    base = dict(ink=WHITE, ink2=MIST, accent=SKY, onacc=NAVY, hi=YEL, head2=YEL, cta2=YEL, eyebrow=("fill", SKY, WHITE), btn=(SKY, WHITE),
                tagnew=(YEL, NAVY), tagother=(SKY, NAVY), num=SKY, numstyle="big", rule=None, mark=False, tagline=None)
    base.update(k); return base


PAL = {
    "navy": P(),
    "light": P(ink=NAVY, ink2=SLATE, accent=BLUE, onacc=WHITE, head2=BLUE, cta2=BLUE, eyebrow=("outline", NAVY, NAVY), btn=(NAVY, WHITE),
               tagother=(NAVY, WHITE), num=BLUE, rule=YEL, mark=True),
    "cards": P(ink=NAVY, ink2=SLATE, accent=BLUE, onacc=WHITE, head2=BLUE, cta2=BLUE, btn=(NAVY, WHITE), tagother=(NAVY, WHITE), num=BLUE, numstyle="badge"),
    "bold_dark": P(ink2=(214, 228, 245), accent=YEL, onacc=NAVY, eyebrow=("text", YEL, YEL), btn=(YEL, NAVY), numstyle="label", tagline=WHITE),
    "bold_yel": P(ink=NAVY, ink2=NAVYM, accent=BLUE, onacc=WHITE, hi=NAVY, head2=BLUE, cta2=BLUE, eyebrow=("text", NAVY, NAVY), btn=(NAVY, WHITE),
                  numstyle="label", tagline=NAVY, num=BLUE),
    "holiday": P(ink2=(232, 222, 205), accent=GOLD, onacc=NAVY2, hi=RED, head2=GOLD, cta2=GOLD, eyebrow=("fill", RED, WHITE), btn=(GOLD, NAVY2),
                 tagnew=(GOLD, NAVY2), tagother=(RED, WHITE), num=GOLD),
    "shopsmall": P(ink=NAVY, ink2=SLATE, accent=RED, onacc=WHITE, hi=RED, head2=RED, cta2=RED, eyebrow=("fill", RED, WHITE), btn=(RED, WHITE),
                   tagnew=(YEL, NAVY), tagother=(NAVY, WHITE), num=RED, rule=RED),
    "yearend": P(ink2=(214, 206, 186), accent=GOLD, onacc=NAVY2, hi=GOLD, head2=GOLD, cta2=GOLD, eyebrow=("outline", GOLD, GOLD), btn=(GOLD, NAVY2),
                 tagnew=(GOLD, NAVY2), tagother=(GOLD, NAVY2), num=GOLD),
}


# ------------------------------------------------------------------ content drawers: f(d, x, y, w, F, P, lt, ctx) -> height
def _eyebrow(d, x, y, text, F, p):
    mode, c1, c2 = p["eyebrow"]
    if mode == "text":
        d.text((x, y), text, font=F.small, fill=c1); return F.small.size * 1.3
    _, h = pill(d, x, y, text, F.pill, c1, c2, outline=c1 if mode == "outline" else None); return h


def draw_intro(d, x, y, w, F, p, lt, c):
    y0 = y; sp = c["spec"]
    y += _eyebrow(d, x, y, sp.get("eyebrow", "HIGHLEVEL THIS WEEK"), F, p) + F.head.size * 0.45
    hf = F.head if not p.get("big") else O(800, F.head.size * 1.12)
    for ln in wrap(d, sp.get("head1", "What's new"), hf, w): d.text((x, y), ln, font=hf, fill=p["ink"]); y += hf.size * 1.06
    for ln in wrap(d, sp.get("head2", "in HighLevel"), hf, w):
        if p["mark"]:
            hw = d.textlength(ln, font=hf) * ease((lt - 0.5) / 0.7)
            if hw > 0: d.rectangle((x - 8, y + hf.size * 0.55, x + hw + 8, y + hf.size * 1.02), fill=YEL)
        d.text((x, y), ln, font=hf, fill=p["head2"]); y += hf.size * 1.06
    y += F.head.size * 0.25
    if p["numstyle"] in ("label", "badge"):
        d.rectangle((x, y, x + 150 * F.s * ease((lt - 0.3) / 0.5), y + 12 * F.s), fill=p["hi"] if p["numstyle"] == "label" else YEL); y += 46 * F.s
    if sp.get("week"):
        d.text((x, y), sp["week"], font=F.why, fill=p["ink2"]); y += F.why.size * 1.55
    for ln in wrap(d, sp.get("sub2", ""), F.why, w): d.text((x, y), ln, font=F.why, fill=p["ink"]); y += F.why.size * 1.4
    return y - y0


def draw_outro(d, x, y, w, F, p, lt, c):
    y0 = y; sp = c["spec"]
    for ln in wrap(d, sp.get("cta") or "Want this set up for your business?", F.head, w): d.text((x, y), ln, font=F.head, fill=p["ink"]); y += F.head.size * 1.08
    y += F.head.size * 0.25
    for ln in wrap(d, sp.get("cta2", "We'll handle the setup."), F.title, w): d.text((x, y), ln, font=F.title, fill=p["cta2"]); y += F.title.size * 1.12
    y += F.title.size * 0.45
    _, h = pill(d, x, y, sp.get("button", "Book a call: lewismarketingoc.com"), S(600, F.small.size * 1.1), *p["btn"])
    return y + h - y0


def _head(d, x, y, w, F, p, c, label=None):
    """number / tag row for a body scene; returns height"""
    i, n, tag = c["i"], c["n"], c.get("tag")
    if p["numstyle"] == "big":
        num = f"{i + 1:02d}"; d.text((x, y), num, font=F.num, fill=p["num"])
        nx = x + d.textlength(num, font=F.num) + 30 * F.s
        if tag:
            t = tag.upper(); pill(d, nx, y + F.num.size * 0.38, t, F.pill, *(p["tagnew"] if t == "NEW" else p["tagother"]))
        d.text((x + w, y + F.num.size * 0.5), label or f"{i + 1} of {n}", font=F.small, fill=p["ink2"], anchor="rm")
        return F.num.size * 1.12
    if p["numstyle"] == "badge":
        r = 52 * F.s; d.ellipse((x, y, x + r * 2, y + r * 2), fill=SKY)
        d.text((x + r, y + r), str(i + 1), font=O(800, 60 * F.s), fill=WHITE, anchor="mm")
        if tag:
            t = tag.upper(); pill(d, x + r * 2 + 24 * F.s, y + r - F.pill.size / 2 - 11, t, F.pill, *(p["tagnew"] if t == "NEW" else p["tagother"]))
        d.text((x + w, y + r), label or f"{i + 1} of {n}", font=F.small, fill=p["ink2"], anchor="rm")
        return r * 2 + 44 * F.s
    head = (label or f"{c.get('word') or 'UPDATE'} {i + 1} OF {n}").upper()
    d.text((x, y), head, font=F.small, fill=p["ink2"])
    if tag: pill(d, x + d.textlength(head, font=F.small) + 26, y - 10, tag.upper(), F.pill, None, p["tagline"] or p["ink"], outline=p["tagline"] or p["ink"])
    return F.small.size * 2.6


def _body(d, x, y, w, F, p, text, lines=5):
    y0 = y; ww = w - (40 * F.s if p["rule"] else 0); xx = x + (40 * F.s if p["rule"] else 0)
    for ln in wrap(d, text, F.why, ww)[:lines]: d.text((xx, y), ln, font=F.why, fill=p["ink2"]); y += F.why.size * 1.45
    if p["rule"] and y > y0: d.rectangle((x, y0 + 6, x + 8 * F.s, y - F.why.size * 0.45), fill=p["rule"])
    return y - y0


def _bar(d, x, y, F, p, lt):
    if p["rule"]: return 28 * F.s
    d.rectangle((x, y + 20 * F.s, x + 110 * F.s * ease((lt - 0.2) / 0.4), y + 30 * F.s), fill=p["hi"]); return 66 * F.s


def draw_item(d, x, y, w, F, p, lt, c):
    it = c["item"]; y0 = y; y += _head(d, x, y, w, F, p, c)
    tf = F.title if p["numstyle"] != "label" else O(800, F.title.size * 1.15)
    for ln in wrap(d, it["title"], tf, w)[:4]: d.text((x, y), ln, font=tf, fill=p["ink"]); y += tf.size * 1.1
    y += _bar(d, x, y, F, p, lt)
    y += _body(d, x, y, w, F, p, it.get("why", ""), 5 if c["L"].v else 3)
    return y - y0


def draw_myth(d, x, y, w, F, p, lt, c):
    it = c["item"]; y0 = y; rv = c.get("reveal", 2.0)
    _, h = pill(d, x, y, "MYTH", F.pill, None, p["ink2"], outline=p["ink2"]); y += h + 24 * F.s
    mf = O(700, F.title.size * 0.82); k = ease((lt - (rv - 0.7)) / 0.5)
    for ln in wrap(d, it["myth"], mf, w)[:4]:
        d.text((x, y), ln, font=mf, fill=p["ink2"])
        if k > 0: d.line((x - 6, y + mf.size * 0.62, x - 6 + (d.textlength(ln, font=mf) + 12) * k, y + mf.size * 0.62), fill=p["accent"], width=max(5, int(7 * F.s)))
        y += mf.size * 1.12
    y += 40 * F.s; a = ease((lt - rv) / 0.45)
    if a > 0:
        _, h = pill(d, x, y, "FACT", F.pill, p["accent"], p["onacc"])
        y += h + 24 * F.s
        for ln in wrap(d, it["fact"], F.title, w)[:5]: d.text((x, y), ln, font=F.title, fill=p["ink"] + (int(255 * a),)); y += F.title.size * 1.1
    else:
        y += F.pill.size + 46 + 24 * F.s + len(wrap(d, it["fact"], F.title, w)[:5]) * F.title.size * 1.1
    return y - y0


def draw_ba(d, x, y, w, F, p, lt, c):
    it = c["item"]; after = c["after"]; y0 = y
    lab = "AFTER" if after else "BEFORE"
    _, h = pill(d, x, y, lab, F.pill, p["accent"], p["onacc"]) if after else pill(d, x, y, lab, F.pill, None, p["ink2"], outline=p["ink2"])
    y += h + 30 * F.s
    for ln in wrap(d, it["title"], F.title, w)[:3]: d.text((x, y), ln, font=F.title, fill=p["ink"]); y += F.title.size * 1.1
    y += 30 * F.s; s = F.why.size * 0.8
    for k, pt in enumerate(it.get("points", [])[:5]):
        a = ease((lt - 0.5 - 0.35 * k) / 0.35)
        lines = wrap(d, pt, F.why, w - s * 2.2)[:2]
        if a > 0:
            (check if after else cross)(d, x, y + F.why.size * 0.35, s, p["accent"] if after else p["ink2"])
            for j, ln in enumerate(lines): d.text((x + s * 2.2, y + j * F.why.size * 1.35), ln, font=F.why, fill=p["ink"] + (int(255 * a),))
        y += len(lines) * F.why.size * 1.35 + F.why.size * 0.6
    return y - y0


def _countup(value, k):
    m = re.match(r"^([^\d]*)([\d,]*\.?\d+)(.*)$", str(value))
    if not m: return str(value)
    pre, num, post = m.groups(); dec = len(num.split(".")[1]) if "." in num else 0
    v = float(num.replace(",", "")) * k
    s = f"{v:,.{dec}f}" if "," in num else f"{v:.{dec}f}"
    return pre + s + post


def draw_stat(d, x, y, w, F, p, lt, c):
    it = c["item"]; y0 = y
    y += _head(d, x, y, w, F, dict(p, numstyle="label" if p["numstyle"] == "big" else p["numstyle"]), dict(c, tag=None, word=c.get("word", "STAT")))
    big = O(800, F.num.size * 1.05)
    while d.textlength(str(it["value"]), font=big) > w and big.size > 60: big = O(800, big.size * 0.9)
    d.text((x, y), _countup(it["value"], ease(lt / 1.2)), font=big, fill=p["accent"]); y += big.size * 1.12
    for ln in wrap(d, it["label"], F.title, w)[:4]: d.text((x, y), ln, font=F.title, fill=p["ink"]); y += F.title.size * 1.1
    y += 26 * F.s
    src = it.get("source") or c.get("footnote")
    if src:
        for ln in wrap(d, ("Source: " + src) if it.get("source") else src, F.small, w)[:3]: d.text((x, y), ln, font=F.small, fill=p["ink2"]); y += F.small.size * 1.4
    return y - y0


def draw_review(d, x, y, w, F, p, lt, c):
    it = c["item"]; y0 = y; r = 26 * F.s
    for k in range(int(it.get("stars", 5))):
        if lt > 0.2 + k * 0.12: star(d, x + r + k * r * 2.4, y + r, r, YEL if p["hi"] != NAVY else NAVY)
    y += r * 2 + 30 * F.s
    d.text((x - 6, y - 20 * F.s), "“", font=O(800, F.num.size * 0.7), fill=p["accent"]); y += F.num.size * 0.32
    qf = O(700, F.title.size * 0.66)
    for ln in wrap(d, it["text"], qf, w)[:8]: d.text((x, y), ln, font=qf, fill=p["ink"]); y += qf.size * 1.3
    y += 24 * F.s
    d.text((x, y), "- " + it.get("name", ""), font=O(700, F.why.size), fill=p["ink"]); y += F.why.size * 1.4
    d.text((x, y), it.get("source", "Google review"), font=F.small, fill=p["ink2"]); y += F.small.size * 1.4
    return y - y0


def draw_quote(d, x, y, w, F, p, lt, c):
    """podcast quote scene with waveform"""
    ep = c["spec"].get("episode", {}); y0 = y
    d.text((x, y), (ep.get("show") or "The Marketing Lens").upper(), font=F.small, fill=p["ink2"]); y += F.small.size * 2
    env = c.get("env"); bars = 28; bw = w / bars; bh = 90 * F.s
    for k in range(bars):
        if env is not None and len(env):
            v = env[min(len(env) - 1, max(0, int(c["t"] * FPS) - k % 5))]
            amp = 0.15 + 0.85 * v * (0.6 + 0.4 * math.sin(k * 1.7))
        else:
            amp = 0.25 + 0.75 * abs(math.sin(lt * 5 + k * 0.7) * math.sin(lt * 2.3 + k * 0.31))
        hh = max(6, bh * amp); cx = x + k * bw + bw / 2
        d.rounded_rectangle((cx - bw * 0.3, y + bh / 2 - hh / 2, cx + bw * 0.3, y + bh / 2 + hh / 2), radius=int(bw * 0.3), fill=p["accent"])
    y += bh + 40 * F.s
    qf = O(700, F.title.size * 0.8)
    for ln in wrap(d, "“" + ep.get("quote", "") + "”", qf, w)[:6]: d.text((x, y), ln, font=qf, fill=p["ink"]); y += qf.size * 1.2
    y += 20 * F.s
    if ep.get("guest"): d.text((x, y), "- " + ep["guest"], font=O(700, F.why.size), fill=p["ink2"]); y += F.why.size * 1.4
    return y - y0


def draw_countdown(d, x, y, w, F, p, lt, c):
    ev = c["spec"].get("event", {}); days = c["days"]; y0 = y
    k = ease(lt / 1.3); shown = round(days + 7 * (1 - k))
    big = O(800, F.num.size * 1.35); d.text((x, y), str(shown), font=big, fill=p["accent"]); y += big.size * 1.05
    d.text((x, y), "DAY TO GO" if days == 1 else "DAYS TO GO", font=O(800, F.title.size * 0.8), fill=p["ink"]); y += F.title.size * 1.2
    y += _bar(d, x, y, F, p, lt)
    for ln in wrap(d, ev.get("name", ""), F.title, w)[:3]: d.text((x, y), ln, font=F.title, fill=p["ink"]); y += F.title.size * 1.1
    return y - y0


def draw_details(d, x, y, w, F, p, lt, c):
    ev = c["spec"].get("event", {}); y0 = y
    _, h = pill(d, x, y, "SAVE THE DATE", F.pill, p["accent"], p["onacc"]); y += h + 30 * F.s
    for ln in wrap(d, ev.get("name", ""), F.title, w)[:3]: d.text((x, y), ln, font=F.title, fill=p["ink"]); y += F.title.size * 1.1
    y += 30 * F.s
    rows = [r for r in (_nice_date(ev.get("date")), ev.get("time"), ev.get("place")) if r]
    for k, r in enumerate(rows):
        a = ease((lt - 0.3 - 0.3 * k) / 0.35)
        d.rectangle((x, y + F.why.size * 0.25, x + 10 * F.s, y + F.why.size * 1.05), fill=p["hi"])
        for j, ln in enumerate(wrap(d, r, O(700, F.why.size * 1.1), w - 34 * F.s)[:2]):
            d.text((x + 34 * F.s, y), ln, font=O(700, F.why.size * 1.1), fill=p["ink"] + (int(255 * a),)); y += F.why.size * 1.45
        y += F.why.size * 0.4
    return y - y0


def _nice_date(s):
    if not s: return None
    try: return datetime.date.fromisoformat(s).strftime("%A, %B %-d, %Y")
    except ValueError: return s


# ------------------------------------------------------------------ scenes per format
def build_scenes(spec):
    fmt = spec.get("format", "list"); sc = [dict(kind="intro", draw=draw_intro, dur=3.2, body=False)]
    vo = spec.get("vo", {}) if isinstance(spec.get("vo"), dict) else {}

    def add(draw, dur, item=None, **k):
        sc.append(dict(kind="body", draw=draw, dur=dur, body=True, item=item, **k))
    if fmt == "list":
        for it in spec["items"]: add(draw_item, 4.6, it, tag=it.get("tag"), vo=it.get("vo") or f"{it['title']}. {it.get('why', '')}")
    elif fmt == "myth":
        for it in spec["items"]: add(draw_myth, 6.0, it, vo=it.get("vo") or f"Myth: {it['myth']} Fact: {it['fact']}", word="MYTH")
    elif fmt == "beforeafter":
        b, a = spec["before"], spec["after"]
        add(draw_ba, 5.5, b, after=False, vo=b.get("vo") or "Before. " + b["title"] + ". " + ". ".join(b.get("points", [])) + ".")
        add(draw_ba, 5.5, a, after=True, vo=a.get("vo") or "After. " + a["title"] + ". " + ". ".join(a.get("points", [])) + ".")
    elif fmt in ("stat", "results"):
        foot = None
        if fmt == "results": foot = spec.get("footnote") or f"Combined results across Lewis Marketing clients, {spec.get('month', '')}".strip(", ")
        for it in spec["stats"]:
            if fmt == "stat": assert it.get("source"), "every stat needs a credible source"
            add(draw_stat, 5.0, it, footnote=foot, word="RESULT" if fmt == "results" else "STAT",
                vo=it.get("vo") or f"{it['value']} {it['label']}." + (f" Source: {it['source']}." if it.get("source") else ""))
    elif fmt == "review":
        for it in spec["reviews"]:
            add(draw_review, max(6.0, 3.0 + len(it["text"]) / 22), it, vo=it.get("vo") or f"{it.get('stars', 5)} stars from {it.get('name', '')}. {it['text']}")
    elif fmt == "podcast":
        ep = spec.get("episode", {})
        add(draw_quote, max(7.0, 3.0 + len(ep.get("quote", "")) / 18), ep, vo=ep.get("vo") or (None if spec.get("audio") else f"{ep.get('quote', '')}"))
    elif fmt == "countdown":
        ev = spec["event"]; pd = datetime.date.fromisoformat(spec.get("postDate") or datetime.date.today().isoformat())
        days = (datetime.date.fromisoformat(ev["date"]) - pd).days; assert days >= 0, "event date is before postDate"
        add(draw_countdown, 4.6, ev, days=days, vo=f"{days} days until {ev['name']}.")
        add(draw_details, 5.0, ev, vo=", ".join(r for r in (_nice_date(ev.get("date")), ev.get("time"), ev.get("place")) if r) + ".")
    else:
        raise SystemExit(f"unknown format {fmt}")
    sc.append(dict(kind="outro", draw=draw_outro, dur=4.2, body=False))
    n = sum(1 for s in sc if s["body"]); i = 0
    for s in sc:
        if s["body"]: s["i"] = i; s["n"] = n; i += 1
    sc[0]["vo"] = vo.get("intro") or " ".join(t for t in (spec.get("head1", "What's new"), spec.get("head2", "in HighLevel")) if t).rstrip(".") + ". " + spec.get("sub2", "")
    btn = spec.get("button", "Book a call: lewismarketingoc.com").replace(":", " at")
    sc[-1]["vo"] = vo.get("outro") or f"{spec.get('cta') or ''} {spec.get('cta2', '')} {btn}."
    return sc


def defaults(spec):
    fmt = spec.get("format", "list"); sp = dict(spec)
    d = {
        "myth": dict(eyebrow="MYTH VS FACT", head1="Marketing myths", head2="we hear every week"),
        "beforeafter": dict(eyebrow="BEFORE AND AFTER", head1="What changes", head2="when it's set up right"),
        "stat": dict(eyebrow="BY THE NUMBERS", head1="Numbers worth", head2="knowing"),
        "results": dict(eyebrow="RESULTS", head1="What our clients", head2=f"saw in {spec.get('month', 'a month')}", sub2="Combined across Lewis Marketing clients."),
        "review": dict(eyebrow="CLIENT LOVE", head1="Don't take", head2="our word for it"),
        "countdown": dict(eyebrow="COUNTDOWN", head1=spec.get("event", {}).get("name", ""), head2="is almost here"),
    }.get(fmt, {})
    if fmt == "podcast":
        ep = spec.get("episode", {})
        d = dict(eyebrow=(ep.get("show") or "The Marketing Lens").upper(), head1=f"Episode {ep['number']}" if ep.get("number") else "New episode",
                 head2=ep.get("title", ""), week=("With " + ep["guest"]) if ep.get("guest") else "", sub2="",
                 cta="Listen to the full episode", cta2="The Marketing Lens", button="Watch on YouTube: @lewismarketingoc")
    for k, v in d.items(): sp.setdefault(k, v)
    if fmt != "list": sp.setdefault("week", ""); sp.setdefault("sub2", "")
    return sp


# ------------------------------------------------------------------ styles
class Style:
    name = "navy"; page = "reel-generic.html"; png = "howie-pointL.png"; logo = "white"; site = MIST

    def __init__(self, L):
        self.L = L; self.base = self.bg(L.W, L.H); self.footer(self.base)

    def pal(self, i): return PAL[self.name]

    def bg(self, W, H):
        y, x = np.mgrid[0:H, 0:W]; cx, cy = W * 0.72, H * 0.22
        r = np.sqrt(((x - cx) / W) ** 2 + ((y - cy) / H) ** 2); g = np.clip(1 - r * 1.6, 0, 1)[..., None]
        im = Image.fromarray((np.array(NAVY2, float) * (1 - g) + np.array(NAVY, float) * g).astype(np.uint8)).convert("RGBA")
        glow = Image.new("RGBA", (W, H)); ImageDraw.Draw(glow).ellipse((W * 0.55, -H * 0.15, W * 1.1, H * 0.45), fill=SKY + (60,))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W // 8)))
        arcs = Image.new("RGBA", (W, H)); ad = ImageDraw.Draw(arcs); cx, cy = W * 1.02, -H * 0.04; b = min(W, H) * 0.22
        for k in range(5):
            rr = b + k * min(W, H) * 0.075; ad.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=SKY + (34 - k * 5,), width=2)
        im.alpha_composite(arcs); ImageDraw.Draw(im).rectangle((0, 0, 10 if W > H else 12, H), fill=SKY)
        vig = np.zeros((H, W, 4), np.uint8); vig[..., 3] = (np.clip((np.arange(H) - H * 0.7) / (H * 0.3), 0, 1) * 70)[:, None].astype(np.uint8); vig[..., :3] = NAVY2
        im.alpha_composite(Image.fromarray(vig, "RGBA")); return im

    def footer(self, im, logo=None, site=None):
        L = self.L; d = ImageDraw.Draw(im); logo = logo or self.logo; site = site or self.site
        paste_logo(im, L.W / 2 if L.v else L.x0, L.foot - (10 if L.v else 30), L.logo, logo, "c" if L.v else "l")
        if L.v: d.text((L.W / 2, L.foot + L.logo + 14), "lewismarketingoc.com", font=S(600, L.site), fill=site, anchor="mm")
        else: d.text((L.W - 110, L.foot - 3), "lewismarketingoc.com", font=S(600, L.site), fill=site, anchor="rm")

    def scene_bg(self, sc, si, lt): return self.base.copy()

    def decorate(self, im, sc, si, lt, t, total):
        L = self.L; d = ImageDraw.Draw(im)
        pts = [(k / 40 * L.W, L.H - 26 - (math.sin(k / 40 * 7) * 6 + k / 40 * 50)) for k in range(41) if k / 40 <= t / total * 1.05]
        if len(pts) > 1: d.line(pts, fill=SKY + (170,), width=5)
        self.dots(d, sc, si, YEL, (255, 255, 255, 60))

    def dots(self, d, sc, si, on, off):
        s = sc[si]
        if not s["body"] or s["n"] < 2: return
        L = self.L; n = s["n"]
        for j in range(n):
            cx = (L.W / 2 - (n - 1) * 18 + j * 36) if L.v else (L.x0 + j * 30 + 8); cy = L.prog if L.v else L.foot - 120
            d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=on if j == s["i"] else off)

    def box(self):
        L = self.L; return L.x0, L.top, L.x1 - L.x0, L.bottom - L.top

    def place(self, im, layer, sc, si, lt, last):
        dur = sc[si]["dur"]; a = ease(lt / 0.45) * (1 if last else 1 - ease((lt - dur + 0.35) / 0.35))
        im.alpha_composite(shift(alpha(layer, a), dy=int((1 - ease(lt / 0.45)) * 50)))

    def gbp_bg(self, W, H): return self.bg(W, H)


class Light(Style):
    name = "light"; logo = "color"; site = SLATE

    def bg(self, W, H):
        im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
        if hasattr(self, "L") and self.L.howie and (W, H) == (self.L.W, self.L.H):
            cx, cy, r = self.L.disc
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(214, 233, 245)); d.ellipse((cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26), outline=(190, 220, 240), width=3)
        d.rectangle((0, 0, W, 14), fill=NAVY); d.rectangle((0, 0, W * 0.28, 14), fill=SKY); d.rectangle((W * 0.28, 0, W * 0.36, 14), fill=YEL)
        return im

    def decorate(self, im, sc, si, lt, t, total):
        s = sc[si]
        if not s["body"] or s["n"] < 2: return
        L = self.L; d = ImageDraw.Draw(im); n = s["n"]; gap = 14; seg = ((L.x1 - L.x0) - gap * (n - 1)) / n; py = L.prog
        for j in range(n):
            x = L.x0 + j * (seg + gap); d.rounded_rectangle((x, py, x + seg, py + 10), radius=5, fill=LINE)
            p = 1 if j < s["i"] else (min(1, lt / (s["dur"] - 0.3)) if j == s["i"] else 0)
            if p > 0: d.rounded_rectangle((x, py, x + max(10, seg * p), py + 10), radius=5, fill=SKY)


class Bold(Style):
    name = "bold"

    def __init__(self, L): self.L = L; self.base = None

    def fields(self, sc):
        cyc = [BLUE, YEL, NAVY]; f = [NAVY] + [cyc[i % 3] for i in range(len(sc) - 2)]
        f.append(BLUE if f[-1] == YEL else YEL); return f

    def pal(self, i):
        p = PAL["bold_yel"] if self._f[i] == YEL else PAL["bold_dark"]; return dict(p, big=True)

    def scene_bg(self, sc, si, lt):
        L = self.L; W, H = L.W, L.H; self._f = f = self.fields(sc); col = f[si]; prev = f[si - 1] if si else col
        im = Image.new("RGBA", (W, H), prev + (255,)); d = ImageDraw.Draw(im)
        p = 1 if si == 0 else ease(lt / 0.55); sl = H * 0.18; xl = W + sl - p * (W + sl * 2)
        d.polygon([(xl + sl, 0), (W + 10, 0), (W + 10, H), (xl, H)], fill=col)
        if p < 1:
            acc = YEL if col != YEL else WHITE
            d.polygon([(xl + sl - 22, 0), (xl + sl, 0), (xl, H), (xl - 22, H)], fill=acc)
        if p >= 0.98: self.footer(im, NAVY if col == YEL else "white", NAVYM if col == YEL else (214, 228, 245))
        return im

    def decorate(self, im, sc, si, lt, t, total):
        s = sc[si]
        if not s["body"] or self.L.key in ("45", "11"): return
        L = self.L; col = self._f[si]; g = Image.new("RGBA", (L.W, L.H)); gd = ImageDraw.Draw(g)
        gf = O(800, {"916": 660, "169": 520, "45": 430, "11": 330}[L.key])
        gx = L.W + 40 - (1 - ease((lt - 0.35) / 0.7)) * 120
        gd.text((gx, L.H - (60 if L.v else 40)), f"{s['i'] + 1:02d}", font=gf,
                fill=(NAVY + (34,)) if col == YEL else (WHITE + (30,)), anchor="rd")
        im.alpha_composite(g)

    def box(self):
        L = self.L; return L.x0, L.top, (L.x1 if L.v else 1250) - L.x0, L.bottom - L.top

    def place(self, im, layer, sc, si, lt, last):
        tl = lt - (0.35 if si else 0); dur = sc[si]["dur"]
        a = ease(tl / 0.3) * (1 if last else 1 - ease((lt - dur + 0.3) / 0.3))
        im.alpha_composite(shift(alpha(layer, a), dx=-int((1 - ease(tl / 0.5)) * 140)))

    def gbp_bg(self, W, H):
        im = Image.new("RGBA", (W, H), BLUE + (255,)); d = ImageDraw.Draw(im)
        d.polygon([(W * 0.72, 0), (W, 0), (W, H), (W * 0.6, H)], fill=NAVY)
        d.polygon([(W * 0.72 - 18, 0), (W * 0.72, 0), (W * 0.6, H), (W * 0.6 - 18, H)], fill=YEL); return im


class Cards(Style):
    name = "cards"

    def bg(self, W, H):
        y = np.linspace(0, 1, H)[:, None, None]
        img = np.array(NAVY, float) * (1 - y) + np.array(NAVY2, float) * y
        im = Image.fromarray(np.broadcast_to(img, (H, W, 3)).astype(np.uint8)).convert("RGBA")
        glow = Image.new("RGBA", (W, H)); ImageDraw.Draw(glow).ellipse((W * 0.25, -H * 0.2, W * 1.05, H * 0.35), fill=SKY + (55,))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W // 8))); return im

    def pad(self): return {"916": 64, "169": 56, "45": 52, "11": 44}[self.L.key]

    def box(self):
        L = self.L; p = self.pad(); return L.x0 - 30 + p, L.top + p, (L.x1 - L.x0 + 60) - 2 * p, L.bottom - L.top - 2 * p

    def card(self, layer, h):
        """wrap the content layer in a white card with shadow"""
        L = self.L; p = self.pad(); x0, x1 = L.x0 - 30, L.x1 + 30; top = L.top + max(0, (L.bottom - L.top - h - 2 * p) * 0.3)
        im = Image.new("RGBA", (L.W, L.H)); sh = Image.new("RGBA", (L.W, L.H))
        ImageDraw.Draw(sh).rounded_rectangle((x0, top + 18, x1, top + h + 2 * p + 18), radius=40, fill=(0, 0, 0, 120))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
        ImageDraw.Draw(im).rounded_rectangle((x0, top, x1, top + h + 2 * p), radius=40, fill=WHITE)
        im.alpha_composite(shift(layer, dy=int(top + p - (L.top + p))))
        return im, top

    def decorate(self, im, sc, si, lt, t, total):
        s = sc[si]; L = self.L
        if not s["body"] or s["i"] == 0: return
        d = ImageDraw.Draw(im); top = getattr(self, "_top", L.top)
        for k in range(min(s["i"], 2), 0, -1):
            inset = 36 * k; yy = top - 34 * k
            d.rounded_rectangle((L.x0 - 30 + inset, yy, L.x1 + 30 - inset, yy + 200), radius=36, fill=(200, 212, 228) if k == 2 else (226, 233, 242))

    def place(self, im, layer, sc, si, lt, last):
        dur = sc[si]["dur"]; kin = ease(lt / 0.5); kout = 0 if last else ease((lt - dur + 0.4) / 0.4)
        a = kin * (1 - kout); sc_ = (0.94 + 0.06 * kin) * (1 - 0.05 * kout)
        c = layer
        if sc_ != 1:
            W, H = c.size; c2 = c.resize((int(W * sc_), int(H * sc_)), Image.BILINEAR); c = Image.new("RGBA", (W, H)); c.alpha_composite(c2, ((W - c2.width) // 2, (H - c2.height) // 2))
        im.alpha_composite(shift(alpha(c, a), dy=int((1 - kin) * 140 - kout * 80)))
        s = sc[si]
        if s["body"] and self.L.v and s["n"] > 1:
            d = ImageDraw.Draw(im); n = s["n"]; px = self.L.W / 2 - (n - 1) * 22; py = self.L.bottom + 45
            for j in range(n):
                cx = px + j * 44; wv = 22 if j == s["i"] else 9
                d.rounded_rectangle((cx - wv, py - 9, cx + wv, py + 9), radius=9, fill=YEL if j == s["i"] else (255, 255, 255, 70))


class Holiday(Style):
    name = "holiday"; page = "reel-santa.html"; png = "howie-santa-wave.png"; site = (232, 222, 205)

    def bg(self, W, H):
        y = np.linspace(0, 1, H)[:, None, None]
        img = np.array((12, 34, 72), float) * (1 - y) + np.array(NIGHT, float) * y
        im = Image.fromarray(np.broadcast_to(img, (H, W, 3)).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
        b = min(W, H) * 0.06  # ribbon wrapping the top-right corner
        d.polygon([(W - b * 5.2, 0), (W - b * 3.6, 0), (W, b * 3.6), (W, b * 5.2)], fill=RED)
        d.polygon([(W - b * 4.6, 0), (W - b * 4.2, 0), (W, b * 4.2), (W, b * 4.6)], fill=GOLD)
        d.rectangle((0, 0, 12, H), fill=GOLD); return im

    def decorate(self, im, sc, si, lt, t, total): self.dots(ImageDraw.Draw(im), sc, si, GOLD, (255, 255, 255, 60))


class ShopSmall(Light):
    name = "shopsmall"

    def bg(self, W, H):
        im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
        if hasattr(self, "L") and self.L.howie and (W, H) == (self.L.W, self.L.H):
            cx, cy, r = self.L.disc; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(246, 220, 222))
        sw = W / 12; ah = max(36, H * 0.03)  # storefront awning
        for k in range(12):
            d.rectangle((k * sw, 0, (k + 1) * sw, ah), fill=RED if k % 2 == 0 else WHITE)
            d.pieslice((k * sw, ah - sw / 2, (k + 1) * sw, ah + sw / 2), 0, 180, fill=RED if k % 2 == 0 else (236, 232, 224))
        return im

    def decorate(self, im, sc, si, lt, t, total):
        s = sc[si]
        if not s["body"] or s["n"] < 2: return
        self.dots(ImageDraw.Draw(im), sc, si, RED, LINE)


class YearEnd(Style):
    name = "yearend"; page = "reel-party.html"; png = "howie-party-cheer.png"; site = (214, 206, 186)

    def bg(self, W, H):
        im = Image.new("RGBA", (W, H), NIGHT + (255,)); d = ImageDraw.Draw(im)
        glow = Image.new("RGBA", (W, H)); ImageDraw.Draw(glow).ellipse((W * 0.5, -H * 0.2, W * 1.15, H * 0.35), fill=GOLD + (40,))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W // 7)))
        for k in range(6):  # thin gold rays from the bottom-right corner, clear of the copy
            a = math.radians(196 + k * 11); r = min(W, H) * 0.42
            d.line([(W, H), (W + r * math.cos(a), H + r * math.sin(a))], fill=GOLD + (80,), width=2)
        d.rectangle((0, 0, 12, H), fill=GOLD); return im

    def decorate(self, im, sc, si, lt, t, total): self.dots(ImageDraw.Draw(im), sc, si, GOLD, (255, 255, 255, 50))


STYLES = {"navy": Style, "light": Light, "bold": Bold, "cards": Cards, "holiday": Holiday, "shopsmall": ShopSmall, "yearend": YearEnd}
ROTATION = ["navy", "light", "bold", "cards"]
_LG = {}


def paste_logo(im, x, y, h, kind, anchor="l"):
    key = (kind if isinstance(kind, str) else tuple(kind), h)
    if key not in _LG:
        if kind == "color": src = Image.open(os.path.join(ENGINE, "logo.png")).convert("RGBA")
        else:
            src = Image.open(os.path.join(ENGINE, "logo_white.png")).convert("RGBA")
            if kind != "white": t = Image.new("RGBA", src.size, tuple(kind) + (255,)); t.putalpha(src.getchannel("A")); src = t
        _LG[key] = src.resize((int(src.width * h / src.height), h), Image.LANCZOS)
    lg = _LG[key]
    if anchor == "c": x -= lg.width // 2
    if anchor == "r": x -= lg.width
    im.alpha_composite(lg, (int(x), int(y)))


# ------------------------------------------------------------------ frame rendering
class Renderer:
    def __init__(self, spec, sc, key, howie, captions):
        self.spec = spec; self.sc = sc; self.L = Layout(key, howie, captions); self.st = STYLES[spec.get("style", "navy")](self.L)
        self.starts = np.cumsum([0] + [s["dur"] for s in sc])[:-1]; self.total = sum(s["dur"] for s in sc); self._fit = {}

    def ctx(self, si, t):
        s = self.sc[si]; return dict(spec=self.spec, L=self.L, i=s.get("i", 0), n=s.get("n", 0), item=s.get("item"), tag=s.get("tag"),
                                     after=s.get("after"), days=s.get("days"), reveal=s.get("reveal", 2.0), footnote=s.get("footnote"),
                                     word=s.get("word"), env=getattr(self, "env", None), t=t)

    def fit(self, si, p):
        if si in self._fit: return self._fit[si]
        x, y, w, h = self.st.box(); probe = ImageDraw.Draw(Image.new("RGBA", (max(4, int(w) + 400), 4000)))
        s = 1.0
        while True:
            F = self.L.fonts(s); hh = self.sc[si]["draw"](probe, 0, 0, w, F, p, 99, self.ctx(si, 0))
            if hh <= h or s < 0.6: break
            s *= 0.92
        self._fit[si] = (F, hh); return self._fit[si]

    def frame(self, t):
        si = int(np.searchsorted(self.starts, t, side="right") - 1); lt = t - self.starts[si]
        st = self.st; im = st.scene_bg(self.sc, si, lt); p = st.pal(si)
        F, hh = self.fit(si, p); x, y, w, h = st.box()
        y = y + max(0, (h - hh) * (0.3 if self.L.v else 0.4))
        layer = Image.new("RGBA", (self.L.W, self.L.H)); self.sc[si]["draw"](ImageDraw.Draw(layer), x, y, w, F, p, lt, self.ctx(si, t))
        if isinstance(st, Cards):
            pad = st.pad(); layer = shift(layer, dy=-int(y - (self.L.top + pad)))
            layer, st._top = st.card(layer, hh)
        st.decorate(im, self.sc, si, lt, t, self.total)
        st.place(im, layer, self.sc, si, lt, si == len(self.sc) - 1)
        if self.L.captions: self.caption(im, t)
        return im

    def caption(self, im, t):
        words = getattr(self, "words", None)
        if not words: return
        cur = [k for k, w in enumerate(words) if w[1] - 0.05 <= t <= w[2] + 0.35]
        if not cur: return
        k = cur[-1]; chunk = next((c for c in self.chunks if c[0] <= k <= c[1]), None)
        if not chunk: return
        x0, y0, x1, fs = self.L.cap; f = O(700, fs); d = ImageDraw.Draw(im)
        toks = [words[j][0] for j in range(chunk[0], chunk[1] + 1)]; txt = " ".join(toks)
        tw = d.textlength(txt, font=f); bw = min(x1 - x0, tw + fs * 1.2); bx = x0 + ((x1 - x0) - bw) / 2 if not self.L.howie else x0
        ov = Image.new("RGBA", im.size); od = ImageDraw.Draw(ov)
        od.rounded_rectangle((bx, y0, bx + bw, y0 + fs * 1.9), radius=int(fs * 0.5), fill=NAVY2 + (225,))
        im.alpha_composite(ov); xx = bx + fs * 0.6
        for j, tok in enumerate(toks):
            col = YEL if chunk[0] + j == k else WHITE
            d.text((xx, y0 + fs * 0.95), tok, font=f, fill=col, anchor="lm"); xx += d.textlength(tok + " ", font=f)

    def set_words(self, words):
        """words: [(text, start, end)] in video time; group into caption chunks that fit the box"""
        self.words = words; self.chunks = []; f = O(700, self.L.cap[3]); d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
        maxw = self.L.cap[2] - self.L.cap[0] - self.L.cap[3] * 1.2; a = 0
        while a < len(words):
            b = a
            while b + 1 < len(words) and words[b + 1][1] - words[b][2] < 0.6 and d.textlength(" ".join(w[0] for w in words[a:b + 2]), font=f) <= maxw \
                    and not re.search(r"[.!?:]$", words[b][0]) and b - a < 5:
                b += 1
            self.chunks.append((a, b)); a = b + 1


def render_base(r, out):
    W, H = r.L.W, r.L.H
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(int(round(r.total * FPS))): p.stdin.write(r.frame(f / FPS).convert("RGB").tobytes())
    p.stdin.close(); p.wait()


def howie_frames(sc, total, tmp, page):
    T = howie_reel.timeline(total); starts = np.cumsum([0] + [s["dur"] for s in sc])
    PO = [dict(t=0, p="idle"), dict(t=0.9, p="wave"), dict(t=2.6, p="idle")]
    MV = [dict(t=0, x=-200, y=1590, s=1.25), dict(t=0.2, x=200, y=1590, s=1.25, d=0.6, h=150)]
    for k, s in enumerate(sc):
        if not s["body"]: continue
        t0 = float(starts[k]); PO += [dict(t=t0 + 0.5, p="pointR", a=100), dict(t=t0 + 2.4, p="idle")]
        MV.append(dict(t=t0 + 2.8, x=225 if s["i"] % 2 else 200, y=1590, s=1.25, d=0.4, h=45))
    PO.append(dict(t=total - sc[-1]["dur"] + 0.4, p="cheer"))
    T = dict(MV=MV, PO=PO, BU=T["BU"]); json.dump(T, open(f"{tmp}/tl.json", "w"))
    pg = os.path.join(TOOLS, "howie", page)
    if not os.path.exists(pg): pg = os.path.join(TOOLS, "howie", "reel-generic.html")
    npm = subprocess.check_output(["npm", "root", "-g"]).decode().strip()
    subprocess.run(["node", os.path.join(TOOLS, "howie", "render_any.js"), pg, f"{tmp}/tl.json", str(total), f"{tmp}/fr"], check=True, env=dict(os.environ, NODE_PATH=npm))
    return T


def compose(base, tmp, L, howie, audio, out):
    if not howie:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", out], check=True); return
    ox, oy, s = L.hz
    ov = f"[1:v]scale=iw*{s}:-1[h];[0:v][h]overlay={ox}:{oy}:eof_action=pass[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-framerate", str(FPS), "-i", f"{tmp}/fr/h%04d.png", "-i", audio,
                    "-filter_complex", ov, "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)


def envelope(path, n):
    """per-frame loudness 0-1 of an audio file (for the podcast waveform)"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "12000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float) / 32768; per = 12000 // FPS
    e = np.array([np.sqrt(np.mean(a[k * per:(k + 1) * per] ** 2)) if k * per < len(a) else 0 for k in range(n)])
    return np.clip(e / (np.percentile(e, 95) + 1e-6), 0, 1)


# ------------------------------------------------------------------ GBP graphic (1200x900)
def summary_lines(spec, sc):
    fmt = spec.get("format", "list")
    if fmt == "list": return [it["title"] for it in spec["items"]]
    if fmt == "myth": return ["Myth: " + spec["items"][0]["myth"], "Fact: " + spec["items"][0]["fact"]]
    if fmt == "beforeafter": return spec["after"].get("points", [])[:4]
    if fmt in ("stat", "results"): return [f"{s['value']}  {s['label']}" for s in spec["stats"]]
    if fmt == "review": r = spec["reviews"][0]; return ["“" + r["text"] + "”", "- " + r.get("name", "")]
    if fmt == "podcast": ep = spec.get("episode", {}); return [x for x in (ep.get("title"), ("With " + ep["guest"]) if ep.get("guest") else None, "“" + ep.get("quote", "") + "”") if x]
    if fmt == "countdown":
        ev = spec["event"]; days = next(s["days"] for s in sc if s.get("days") is not None)
        return [f"{days} days to go", ev["name"]] + [r for r in (_nice_date(ev.get("date")), ev.get("time"), ev.get("place")) if r]
    return []


def gbp_graphic(spec, sc, out, howie):
    W, H = 1200, 900; key = spec.get("style", "navy"); cls = STYLES[key]
    L = Layout("169", False); st = cls.__new__(cls); st.L = L
    im = st.gbp_bg(W, H) if key != "light" and key != "shopsmall" else cls.bg(st, W, H)
    p = PAL["bold_dark"] if key == "bold" else PAL[key] if key in PAL else PAL["navy"]
    d = ImageDraw.Draw(im); x, wmax = 70, (620 if howie else 1000)
    if key == "cards":
        sh = Image.new("RGBA", (W, H)); ImageDraw.Draw(sh).rounded_rectangle((50, 68, 840, 778), radius=36, fill=(0, 0, 0, 120))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22))); d.rounded_rectangle((50, 50, 840, 760), radius=36, fill=WHITE); x, wmax = 100, 680
    if key == "shopsmall": y = 110
    else: y = 70
    mode, c1, c2 = p["eyebrow"]
    if mode == "text": d.text((x, y), spec.get("eyebrow", ""), font=S(600, 28), fill=c1); y += 50
    else: _, h = pill(d, x, y, spec.get("eyebrow", "HIGHLEVEL THIS WEEK"), S(600, 24), c1, c2, outline=c1 if mode == "outline" else None); y += h + 22
    title = spec.get("gbpTitle") or f"{spec.get('head1', '')} {spec.get('head2', '')}".strip()
    for ln in wrap(d, title, O(800, 56), wmax)[:3]: d.text((x, y), ln, font=O(800, 56), fill=p["ink"]); y += 62
    if spec.get("week"): d.text((x, y + 6), spec["week"], font=S(400, 28), fill=p["ink2"]); y += 50
    y += 24
    for k, ln in enumerate(summary_lines(spec, sc)[:5]):
        f = O(700, 30)
        lines = wrap(d, ln, f, wmax - 70)[:3]
        d.text((x, y - 4), f"{k + 1:02d}" if spec.get("format", "list") in ("list",) else "•", font=O(800, 36), fill=p["accent"] if key not in ("bold",) else YEL)
        for j, l in enumerate(lines): d.text((x + 70, y + j * 38), l, font=f, fill=p["ink"])
        y += 38 * len(lines) + 18
        if y > 700: break
    if howie:
        hp = Image.open(os.path.join(TOOLS, "howie", cls.png if os.path.exists(os.path.join(TOOLS, "howie", cls.png)) else "howie-pointL.png")).convert("RGBA")
        hp = hp.resize((int(hp.width * 290 / hp.height), 290), Image.LANCZOS); im.alpha_composite(hp, (W - hp.width - 50, H - hp.height - 130))
    light = key in ("light", "shopsmall")
    paste_logo(im, 70, H - 95, 54, "color" if light else "white")
    d.text((W - 60, H - 68), "lewismarketingoc.com", font=S(600, 26), fill=SLATE if light else MIST if key != "bold" else WHITE, anchor="rm")
    im.convert("RGB").save(out, quality=95)


# ------------------------------------------------------------------ main
def mix_audio(tmp, total, spec, sc, starts, T, voiced):
    src = spec.get("audio")
    if src:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-t", str(total + 0.5), "-ac", "2", "-ar", "44100", f"{tmp}/m.wav"], check=True)
    else:
        music.render(total + 0.5, f"{tmp}/m.wav", spec.get("music", 1))
    if T: howie_reel.sfx(f"{tmp}/m.wav", f"{tmp}/a.wav", T)
    else: subprocess.run(["cp", f"{tmp}/m.wav", f"{tmp}/a.wav"], check=True)
    if voiced:
        ins, filt = [], []
        for k, s in enumerate(sc):
            if s.get("wav"):
                ins += ["-i", s["wav"]]; j = len(ins) // 2
                filt.append(f"[{j}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={int((starts[k] + s['lead']) * 1000)}|{int((starts[k] + s['lead']) * 1000)}[v{j}]")
        nv = len(ins) // 2
        if nv:
            mv = 0.16 if not src else 0.35
            fc = ";".join(filt) + f";[0:a]volume={mv}[bg];" + "".join(f"[v{j}]" for j in range(1, nv + 1)) + f"amix=inputs={nv}:normalize=0[vo];[vo]volume=1.6[vo2];[bg][vo2]amix=inputs=2:normalize=0[out]"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/a.wav", *ins, "-filter_complex", fc, "-map", "[out]", f"{tmp}/a2.wav"], check=True)
            os.replace(f"{tmp}/a2.wav", f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/a.wav", "-af", f"afade=t=out:st={total - 1.5}:d=1.5", f"{tmp}/af.wav"], check=True)


def prepare(spec, tmp, outdir):
    spec = defaults(spec); sc = build_scenes(spec); howie = spec.get("howie", True) is not False
    voiced = bool(spec.get("voice")); words = []
    if voiced:
        import voice
        res = voice.narrate([s.get("vo") for s in sc], tmp, spec.get("voiceName", "af_heart"), spec.get("voiceSpeed", 1.0))
        for s, r in zip(sc, res):
            if not r: continue
            s["wav"] = r["wav"]; s["lead"] = 0.55; s["dur"] = max(s["dur"], s["lead"] + r["dur"] + 0.75); s["words"] = r["words"]
            if s["draw"] is draw_myth:  # reveal the fact as the narrator says "Fact"
                ft = next((w[1] for w in r["words"] if w[0].lower().strip(".:,") == "fact"), None)
                if ft is not None: s["reveal"] = s["lead"] + ft
        json.dump([r.get("check") if r else None for r in res], open(os.path.join(outdir, "voice-check.json"), "w"), indent=1)
    starts = np.cumsum([0] + [s["dur"] for s in sc])[:-1]; total = float(sum(s["dur"] for s in sc))
    for k, s in enumerate(sc):
        for w in s.get("words", []): words.append((w[0], starts[k] + s["lead"] + w[1], starts[k] + s["lead"] + w[2]))
    return spec, sc, howie, voiced, words, starts, total


def main(spec_path, outdir):
    raw = json.load(open(spec_path)); os.makedirs(outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR", "/tmp"))
    spec, sc, howie, voiced, words, starts, total = prepare(raw, tmp, outdir)
    captions = spec.get("captions", voiced) and bool(words)
    style = STYLES[spec.get("style", "navy")]
    T = howie_frames(sc, total, tmp, style.page) if howie else None
    mix_audio(tmp, total, spec, sc, starts, T, voiced)
    env = envelope(f"{tmp}/m.wav", int(total * FPS) + 2) if spec.get("audio") else None
    for key in spec.get("sizes", ["916", "169", "45", "11"]):
        r = Renderer(spec, sc, key, howie, captions); r.env = env
        if captions: r.set_words(words)
        render_base(r, f"{tmp}/b{key}.mp4")
        compose(f"{tmp}/b{key}.mp4", tmp, r.L, howie, f"{tmp}/af.wav", os.path.join(outdir, f"v{key}.mp4"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(sc[0]["dur"] - 0.6), "-i", os.path.join(outdir, f"v{key}.mp4"), "-frames:v", "1", "-q:v", "3",
                        os.path.join(outdir, f"cover{key}.jpg")], check=True)
    gbp_graphic(spec, sc, os.path.join(outdir, "gbp.png"), howie)
    subprocess.run(["rm", "-rf", tmp])
    print(json.dumps({"seconds": round(total, 1), "out": outdir, "style": spec.get("style", "navy"), "format": spec.get("format", "list"), "voice": voiced}))


def preview(spec_path, outdir, sizes=None):
    """stills of every scene (no Howie, no audio) plus gbp.png; uses voice timing only if the spec is not voiced"""
    raw = json.load(open(spec_path)); os.makedirs(outdir, exist_ok=True)
    spec = defaults(raw); sc = build_scenes(spec); howie = spec.get("howie", True) is not False
    for key in sizes or spec.get("sizes", ["916", "169", "45", "11"]):
        r = Renderer(spec, sc, key, howie, False); starts = r.starts
        for k, s in enumerate(sc):
            t = starts[k] + (s["dur"] - 0.5 if s["body"] or k == len(sc) - 1 else s["dur"] - 0.4)
            r.frame(t).convert("RGB").save(f"{outdir}/{key}-{k}.jpg", quality=88)
    gbp_graphic(spec, sc, os.path.join(outdir, "gbp.png"), howie)
