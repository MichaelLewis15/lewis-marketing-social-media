"""Extra Lewis Marketing feed layouts (1080x1350) so graphics don't all look the same.

Every layout takes the same spec fields as render_daily.py (head, sub, rows, bottom, howie, eyebrow)
plus a few optional ones:
  navy    : dark navy, giant headline, yellow highlight words, numbered list.        (good for news, hot takes)
  split   : blue top half with the headline, 2x2 tip cards underneath.                (good for 4-step how-tos)
  number  : one giant number ("big": "4") next to the headline, chip list below.      (good for "3 ways", "5 things")
  note    : handwritten sticky note on a warm desk background.                        (good for quick tips, personal notes)
  myth    : MYTH (crossed out) vs FACT panels; uses "myth" and "fact" strings.          (Myth Monday)
  quote   : one big statement or quote on a blue gradient; uses "quote" and "by".       (quotes, mindset, community)
Headline colour keys: "ink" (main colour for that layout) and "blue" (the accent: yellow on dark layouts, blue on light).
Howie is always drawn (he appears in every Lewis Marketing graphic); pose comes from spec.howie.pose.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import graphics2 as g
from graphics2 import P, W, H, BLUE, BLUE_D, BLUE_L, INK, TEXT, MUTED, LINE, WHITE, RED, GREEN, HEAD, BODY, SEMI, OUTF, SCRIPT, spaced, spaced_len, wrap, shadow

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY = (10, 31, 68); NAVY2 = (6, 18, 42); SUN = (244, 197, 66); MIST = (245, 247, 250); SKY = (41, 162, 222)
LOGO = Image.open(os.path.join(HERE, "logo.png")).convert("RGBA")
LOGO_W = Image.open(os.path.join(HERE, "logo_white.png")).convert("RGBA")


def canvas(col): return Image.new("RGBA", (P(W), P(H)), col + (255,))


def radial(im, cx, cy, r, col, alpha):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), fill=col + (alpha,))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(P(r * .45))))


def dots(im, col, alpha=26, step=36):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for y in range(18, H, step):
        for x in range(18, W, step): d.ellipse((P(x - 1.6), P(y - 1.6), P(x + 1.6), P(y + 1.6)), fill=col + (alpha,))
    im.alpha_composite(lay)


def logo(im, white, x=58, y=None, w=280):
    src = LOGO_W if white else LOGO
    lg = src.resize((P(w), int(P(w) * src.height / src.width)), Image.LANCZOS)
    im.alpha_composite(lg, (P(x), (P(y) if y is not None else P(H - 50) - lg.height)))


def howie(im, hw, default):
    hw = dict(default, **(hw or {}))
    hi = Image.open(os.path.join(HERE, "howie", "howie-%s.png" % hw.get("pose", "wave"))).convert("RGBA")
    hh = P(hw.get("h", 215)); hi = hi.resize((int(hi.width * hh / hi.height), hh), Image.LANCZOS)
    cx, fy = P(hw["x"]), P(hw["feet"])
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((cx - hi.width * .36, fy - P(10), cx + hi.width * .36, fy + P(10)), fill=(10, 31, 68, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(P(6))))
    im.alpha_composite(hi, (int(cx - hi.width / 2), int(fy - hi.height)))


def fit_head(lines, maxw, maxh, start=150, lh=.93, fontf=HEAD):
    size = start
    while size > 40 and (max(fontf(size).getlength(t) for t, _ in lines) > P(maxw) or size * lh * len(lines) > maxh): size -= 2
    return size


def draw_head(d, lines, x, y, size, colmap, lh=.93, fontf=HEAD, center=False):
    f = fontf(size)
    for t, c in lines:
        bb = f.getbbox(t); w = bb[2] - bb[0]
        xx = P(x) - w / 2 if center else P(x)
        d.text((xx - bb[0], P(y) - bb[1]), t, font=f, fill=colmap.get(c, colmap["ink"])); y += size * lh
    return y


def pill(d, x, y, text, bg, fg, size=20, center=False):
    f = SEMI(size); tw = spaced_len(text, f, .18); h = size * 2.1; w = tw / P(1) + size * 1.6
    if center: x = x - w / 2
    d.rounded_rectangle((P(x), P(y), P(x + w), P(y + h)), radius=P(h / 2), fill=bg)
    spaced(d, (P(x + size * .8), P(y + h / 2) - f.getbbox("A")[3] / 2 - P(1)), text, f, fg, .18)
    return y + h


def finish(im, path):
    im.convert("RGB").resize((W, H), Image.LANCZOS).save(path, optimize=True); return path


# ---------------------------------------------------------------- navy
def l_navy(s, path):
    im = canvas(NAVY); radial(im, 300, 380, 520, SKY, 70); radial(im, 950, 1150, 420, SKY, 40); dots(im, (255, 255, 255), 22)
    d = ImageDraw.Draw(im); L = 70
    y = pill(d, L, 70, s.get("eyebrow", "DAILY TIP"), SUN, NAVY, 22) + 34
    size = fit_head(s["head"], 940, 520, 170)
    y = draw_head(d, s["head"], L, y, size, {"ink": WHITE, "blue": SUN, "dark": SKY}) + 14
    for ln in wrap(s["sub"], BODY(36), P(900)): d.text((P(L), P(y)), ln, font=BODY(36), fill=(205, 216, 230)); y += 50
    y += 40; rows = s["rows"][:5]; rh = min(120, (1060 - y) / max(len(rows), 1))
    for i, (_, t) in enumerate(rows):
        d.text((P(L), P(y + 4)), "%02d" % (i + 1), font=HEAD(64), fill=SUN)
        tf = SEMI(36) if len(t) < 34 else SEMI(31)
        d.text((P(L + 110), P(y + 16)), t, font=tf, fill=WHITE)
        d.line([(P(L + 110), P(y + rh - 10)), (P(780), P(y + rh - 10))], fill=(46, 72, 112), width=P(2))
        y += rh
    d.rectangle((0, P(H - 8), P(W), P(H)), fill=SKY)
    logo(im, True, L, None, 280)
    howie(im, s.get("howie"), {"pose": "cheer", "x": 930, "feet": 1290, "h": 240})
    return finish(im, path)


# ---------------------------------------------------------------- split
def l_split(s, path):
    im = canvas(MIST); d = ImageDraw.Draw(im); top = 600
    d.rectangle((0, 0, P(W), P(top)), fill=SKY)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for k in range(-4, 14): ld.line([(P(k * 110), P(top)), (P(k * 110 + 420), 0)], fill=(255, 255, 255, 18), width=P(26))
    im.alpha_composite(lay); d = ImageDraw.Draw(im); L = 64
    y = pill(d, L, 60, s.get("eyebrow", "DAILY TIP"), WHITE, BLUE_D, 20) + 28
    size = fit_head(s["head"], 950, 330, 150)
    y = draw_head(d, s["head"], L, y, size, {"ink": WHITE, "blue": NAVY, "dark": NAVY}) + 12
    for ln in wrap(s["sub"], BODY(30, 600), P(940))[:2]: d.text((P(L), P(y)), ln, font=BODY(30, 600), fill=WHITE); y += 42
    rows = s["rows"][:4]; cw, ch, gx, gy = 461, 245, 30, 28; y0 = top + 36
    for i, (_, t) in enumerate(rows):
        cx = L - 6 + (i % 2) * (cw + gx); cy = y0 + (i // 2) * (ch + gy)
        g.card(im, (cx, cy, cx + cw, cy + ch), radius=24)
        d = ImageDraw.Draw(im)
        d.text((P(cx + 30), P(cy + 18)), str(i + 1), font=HEAD(84), fill=SKY)
        for j, ln in enumerate(wrap(t, SEMI(34), P(cw - 60))[:3]): d.text((P(cx + 30), P(cy + 118 + j * 44)), ln, font=SEMI(34), fill=INK)
    d = ImageDraw.Draw(im)
    if s.get("bottom"):
        bl = wrap(s["bottom"], BODY(30, 600), P(640))[:2]; by = 1182
        for j, ln in enumerate(bl): d.text((P(L), P(by + j * 40)), ln, font=BODY(30, 600), fill=NAVY)
    logo(im, False, L, None, 250)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 960, "feet": top + 8, "h": 200})
    return finish(im, path)


# ---------------------------------------------------------------- number
def l_number(s, path):
    im = canvas(WHITE); radial(im, 1000, 120, 420, BLUE_L[:3], 255); d = ImageDraw.Draw(im); L = 64
    big = str(s.get("big", len(s["rows"])))
    bf = HEAD(470); bb = bf.getbbox(big)
    d.text((P(L) - bb[0], P(60) - bb[1]), big, font=bf, fill=SKY)
    bw = (bb[2] - bb[0]) / P(1)
    hx = L + bw + 40; y = 90
    pill(d, hx, y, s.get("eyebrow", "DAILY TIP"), NAVY, WHITE, 18); y += 70
    size = fit_head(s["head"], W - hx - 60, 360, 110)
    y = draw_head(d, s["head"], hx, y, size, {"ink": INK, "blue": SKY, "dark": BLUE_D})
    y = max(y, 560) + 10
    for ln in wrap(s["sub"], BODY(36), P(950))[:2]: d.text((P(L), P(y)), ln, font=BODY(36), fill=TEXT); y += 50
    y += 34
    for i, (_, t) in enumerate(s["rows"][:5]):
        f = SEMI(35); tw = f.getlength(t) / P(1)
        d.rounded_rectangle((P(L), P(y), P(L + tw + 136), P(y + 88)), radius=P(44), fill=MIST, outline=LINE, width=P(2))
        d.ellipse((P(L + 16), P(y + 16), P(L + 72), P(y + 72)), fill=SKY)
        nf = HEAD(40); nb = nf.getbbox(str(i + 1))
        d.text((P(L + 44) - (nb[0] + nb[2]) / 2, P(y + 44) - (nb[1] + nb[3]) / 2), str(i + 1), font=nf, fill=WHITE)
        d.text((P(L + 94), P(y + 20)), t, font=f, fill=INK); y += 108
    if s.get("bottom"):
        y += 16
        for ln in wrap(s["bottom"].upper(), HEAD(52), P(700))[:2]: d.text((P(L), P(y)), ln, font=HEAD(52), fill=BLUE_D); y += 54
    d.rectangle((0, P(H - 120), P(W), P(H)), fill=NAVY)
    logo(im, True, L, H - 96, 250)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 950, "feet": H - 100, "h": 240})
    return finish(im, path)


# ---------------------------------------------------------------- note
def l_note(s, path):
    im = canvas((236, 228, 214)); dots(im, (120, 100, 70), 18, 28); radial(im, 540, 600, 600, (255, 250, 240), 120)
    note = Image.new("RGBA", (P(860), P(900)), (0, 0, 0, 0)); nd = ImageDraw.Draw(note)
    nd.rectangle((0, 0, P(860), P(900)), fill=(255, 226, 120)); nd.rectangle((0, 0, P(860), P(70)), fill=(250, 214, 96))
    y = 110; size = fit_head(s["head"], 760, 320, 130, 1.0, SCRIPT)
    for t, c in s["head"]:
        nd.text((P(60), P(y)), t, font=SCRIPT(size), fill=NAVY if c == "ink" else (196, 54, 54)); y += size * 1.0
    y += 20
    for i, (_, t) in enumerate(s["rows"][:5]):
        nd.rounded_rectangle((P(60), P(y + 8), P(100), P(y + 48)), radius=P(6), outline=NAVY, width=P(4))
        nd.line([(P(68), P(y + 28)), (P(80), P(y + 42)), (P(108), P(y + 4))], fill=(30, 140, 80), width=P(7))
        for j, ln in enumerate(wrap(t, SCRIPT(58), P(660))[:2]): nd.text((P(128), P(y - 10 + j * 58)), ln, font=SCRIPT(58), fill=NAVY)
        y += 92 + (58 if len(wrap(t, SCRIPT(58), P(660))) > 1 else 0)
    if s.get("bottom"):
        y += 20
        for ln in wrap(s["bottom"], SCRIPT(50), P(740))[:2]: nd.text((P(60), P(y)), ln, font=SCRIPT(50), fill=(196, 54, 54)); y += 54
    sh = Image.new("RGBA", note.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((P(10), P(20), P(860), P(900)), fill=(60, 40, 10, 90))
    sh = sh.rotate(-2.2, resample=Image.BICUBIC, expand=True).filter(ImageFilter.GaussianBlur(P(14)))
    note = note.rotate(-2.2, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(sh, (P(110), P(150))); im.alpha_composite(note, (P(90), P(120)))
    d = ImageDraw.Draw(im)
    tape = Image.new("RGBA", (P(240), P(64)), (255, 255, 255, 150)).rotate(4, expand=True); im.alpha_composite(tape, (P(420), P(96)))
    pill(d, 70, 40, s.get("eyebrow", "QUICK TIP"), NAVY, WHITE, 18)
    logo(im, False, 70, None, 260)
    howie(im, s.get("howie"), {"pose": "wave", "x": 935, "feet": 1300, "h": 250})
    return finish(im, path)


# ---------------------------------------------------------------- myth
def l_myth(s, path):
    im = canvas(MIST); d = ImageDraw.Draw(im); L = 60
    pill(d, L, 56, s.get("eyebrow", "MYTH MONDAY"), NAVY, WHITE, 20)
    myth = s.get("myth") or " ".join(t for t, _ in s["head"]); fact = s.get("fact") or s["sub"]
    g.card(im, (L, 140, W - L, 470), radius=26, fill=(253, 236, 236)); d = ImageDraw.Draw(im)
    d.text((P(L + 40), P(170)), "MYTH", font=HEAD(70), fill=RED)
    mf = HEAD(78 if len(myth) < 34 else 64)
    y = 260
    for ln in wrap('"' + myth + '"', mf, P(W - 2 * L - 80))[:3]:
        d.text((P(L + 40), P(y)), ln, font=mf, fill=(120, 40, 40)); lw = mf.getlength(ln)
        d.line([(P(L + 40), P(y) + mf.getbbox(ln)[3] * .55), (P(L + 40) + lw, P(y) + mf.getbbox(ln)[3] * .55)], fill=RED, width=P(6)); y += mf.size / P(1) * 1.0
    g.card(im, (L, 500, W - L, 1130), radius=26, fill=WHITE); d = ImageDraw.Draw(im)
    d.rectangle((P(L), P(500 + 26), P(L + 14), P(1130 - 26)), fill=GREEN)
    d.text((P(L + 50), P(530)), "FACT", font=HEAD(70), fill=GREEN)
    y = 620
    for ln in wrap(fact, SEMI(42), P(W - 2 * L - 100))[:3]: d.text((P(L + 50), P(y)), ln, font=SEMI(42), fill=INK); y += 56
    y += 34
    for _, t in s["rows"][:4]:
        g.icon(d, "check", L + 72, y + 24, 20, GREEN)
        d.text((P(L + 112), P(y + 2)), t, font=BODY(35), fill=TEXT); y += 90
    logo(im, False, L, None, 260)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 950, "feet": 1300, "h": 220})
    return finish(im, path)


# ---------------------------------------------------------------- quote
def l_quote(s, path):
    im = g.vgrad(P(W), P(H), (12, 40, 86), (24, 120, 176)); radial(im, 540, 560, 460, SKY, 70); dots(im, (255, 255, 255), 18)
    d = ImageDraw.Draw(im)
    pill(d, W / 2, 80, s.get("eyebrow", "WORTH REMEMBERING"), SUN, NAVY, 20, center=True)
    qm = SCRIPT(320); d.text((P(W / 2) - qm.getlength("“") / 2, P(140)), "“", font=qm, fill=SUN)
    q = s.get("quote") or " ".join(t for t, _ in s["head"])
    qf = OUTF(70)
    lines = wrap(q, qf, P(880))
    while len(lines) > 6 and qf.size > P(40): qf = OUTF(qf.size / P(1) - 4); lines = wrap(q, qf, P(880))
    y = 470 - len(lines) * 20
    for ln in lines:
        d.text((P(W / 2) - qf.getlength(ln) / 2, P(y)), ln, font=qf, fill=WHITE); y += qf.size / P(1) * 1.25
    if s.get("by"):
        y += 30; t = "— " + s["by"]; f = SEMI(30); d.text((P(W / 2) - f.getlength(t) / 2, P(y)), t, font=f, fill=(205, 222, 240))
    logo(im, True, W / 2 - 140, None, 280)
    howie(im, s.get("howie"), {"pose": "idle", "x": 920, "feet": 1180, "h": 220})
    return finish(im, path)


LAYOUTS = {"navy": l_navy, "split": l_split, "number": l_number, "note": l_note, "myth": l_myth, "quote": l_quote}


def render(layout, spec, path): return LAYOUTS[layout](spec, path)
