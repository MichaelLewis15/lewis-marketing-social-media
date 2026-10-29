"""Lewis Marketing feed graphics v2: light editorial style (condensed headline, icon rows, bottom-line box, blue wave)."""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("LM_OUT", os.path.join(HERE, "out"))
S = 2                       # supersample factor
W, H = 1080, 1350
def P(v): return int(round(v * S))

BLUE = (41, 162, 222); BLUE_D = (24, 120, 176); BLUE_L = (226, 241, 250); INK = (17, 20, 24)
TEXT = (38, 44, 52); MUTED = (98, 108, 120); LINE = (222, 228, 234); WHITE = (255, 255, 255)
GOLD = (245, 179, 0); RED = (226, 76, 76); GREEN = (34, 160, 90)

def font(name, size): return ImageFont.truetype(os.path.join(HERE, name), P(size))
HEAD = lambda s: font("barlow-condensed-latin-900-normal.woff", s)
BODY = lambda s, w=400: font(f"open-sans-latin-{w}-normal.woff", s)
SEMI = lambda s: font("open-sans-latin-600-normal.woff", s)
OUTF = lambda s: font("outfit-latin-700-normal.woff", s)
SCRIPT = lambda s: font("caveat-latin-700-normal.woff", s)
LOGO = Image.open(os.path.join(HERE, "logo.png")).convert("RGBA")

# ---------- primitives ----------
def spaced(d, xy, text, f, fill, track=0.22):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + f.size * track
    return x

def spaced_len(text, f, track=0.22):
    return sum(f.getlength(c) + f.size * track for c in text) - f.size * track

def wrap(text, f, maxw):
    out, cur = [], ""
    for w_ in text.split():
        t = (cur + " " + w_).strip()
        if f.getlength(t) <= maxw: cur = t
        else: out.append(cur); cur = w_
    out.append(cur); return out

def shadow(im, shape_fn, offset=(0, 18), blur=26, alpha=60):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    shape_fn(ImageDraw.Draw(lay), (20, 40, 60, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(P(blur)))
    im.alpha_composite(lay, (P(offset[0]), P(offset[1])))

def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top)[None, None, :] * (1 - t) + np.array(bot)[None, None, :] * t
    return Image.fromarray(np.broadcast_to(a, (h, w, 3)).astype(np.uint8)).convert("RGBA")

def icon(d, kind, cx, cy, r, col=BLUE, fg=WHITE):
    """Draws a small icon centred at (cx,cy) in unscaled coords; r = half-size."""
    X = lambda v: P(cx + v); Y = lambda v: P(cy + v); lw = max(2, P(r * 0.16))
    if kind == "check":
        d.line([(X(-r*.55), Y(0)), (X(-r*.15), Y(r*.42)), (X(r*.6), Y(-r*.45))], fill=col, width=P(r*.22), joint="curve")
    elif kind == "x":
        for a, b in (((-.5, -.5), (.5, .5)), ((.5, -.5), (-.5, .5))):
            d.line([(X(r*a[0]), Y(r*a[1])), (X(r*b[0]), Y(r*b[1]))], fill=col, width=P(r*.22))
    elif kind == "person":
        d.ellipse((X(-r*.36), Y(-r*.8), X(r*.36), Y(-r*.08)), fill=col)
        d.rounded_rectangle((X(-r*.72), Y(r*.05), X(r*.72), Y(r*.85)), radius=P(r*.45), fill=col)
    elif kind == "phone":
        d.rounded_rectangle((X(-r*.45), Y(-r*.82), X(r*.45), Y(r*.82)), radius=P(r*.18), outline=col, width=lw)
        d.line([(X(-r*.14), Y(r*.6)), (X(r*.14), Y(r*.6))], fill=col, width=lw)
    elif kind == "calendar":
        d.rounded_rectangle((X(-r*.8), Y(-r*.62), X(r*.8), Y(r*.78)), radius=P(r*.16), outline=col, width=lw)
        d.rectangle((X(-r*.8), Y(-r*.62), X(r*.8), Y(-r*.22)), fill=col)
        for gx in (-.4, 0, .4):
            for gy in (.1, .45):
                d.rectangle((X(r*gx - r*.1), Y(r*gy - r*.08), X(r*gx + r*.1), Y(r*gy + r*.1)), fill=col)
        for gx in (-.42, .42):
            d.line([(X(r*gx), Y(-r*.88)), (X(r*gx), Y(-r*.5))], fill=col, width=lw)
    elif kind == "chart":
        for i, h_ in enumerate((.5, .9, 1.4)):
            x0 = -r*.75 + i * r*.55
            d.rounded_rectangle((X(x0), Y(r*.75 - r*h_), X(x0 + r*.38), Y(r*.75)), radius=P(r*.06), fill=col)
    elif kind == "bulb":
        d.ellipse((X(-r*.55), Y(-r*.85), X(r*.55), Y(r*.25)), fill=col)
        d.rectangle((X(-r*.28), Y(r*.15), X(r*.28), Y(r*.55)), fill=col)
        d.line([(X(-r*.25), Y(r*.72)), (X(r*.25), Y(r*.72))], fill=col, width=lw)
    elif kind == "pin":
        d.ellipse((X(-r*.6), Y(-r*.9), X(r*.6), Y(r*.3)), fill=col)
        d.polygon([(X(-r*.5), Y(-r*.05)), (X(r*.5), Y(-r*.05)), (X(0), Y(r*.9))], fill=col)
        d.ellipse((X(-r*.22), Y(-r*.52), X(r*.22), Y(-r*.08)), fill=fg)
    elif kind == "chat":
        d.rounded_rectangle((X(-r*.85), Y(-r*.7), X(r*.85), Y(r*.4)), radius=P(r*.3), fill=col)
        d.polygon([(X(-r*.4), Y(r*.3)), (X(-r*.05), Y(r*.3)), (X(-r*.5), Y(r*.85))], fill=col)
        for gx in (-.4, 0, .4):
            d.ellipse((X(r*gx - r*.1), Y(-r*.25), X(r*gx + r*.1), Y(-r*.05)), fill=fg)
    elif kind == "star":
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5; rr = r * (.9 if k % 2 == 0 else .4)
            pts.append((X(rr * math.cos(ang)), Y(rr * math.sin(ang))))
        d.polygon(pts, fill=col)
    elif kind == "clock":
        d.ellipse((X(-r*.8), Y(-r*.8), X(r*.8), Y(r*.8)), outline=col, width=lw)
        d.line([(X(0), Y(0)), (X(0), Y(-r*.5))], fill=col, width=lw); d.line([(X(0), Y(0)), (X(r*.38), Y(r*.1))], fill=col, width=lw)
    else:  # text glyph (number / letter)
        f = OUTF(r * 1.15); tw = f.getlength(kind); bb = f.getbbox(kind)
        d.text((X(0) - tw / 2, Y(0) - (bb[1] + bb[3]) / 2), kind, font=f, fill=col)

# ---------- page frame ----------
def base():
    im = vgrad(P(W), P(H), (255, 255, 255), (238, 243, 247))
    # soft out-of-focus "office" shapes on the right
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse((P(700), P(-120), P(1250), P(400)), fill=(214, 226, 236, 150))
    d.ellipse((P(820), P(520), P(1200), P(900)), fill=(225, 233, 240, 140))
    d.rounded_rectangle((P(930), P(300), P(1120), P(760)), radius=P(30), fill=(230, 236, 242, 160))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(P(60))))
    return im

def wave(im, tagline):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pts = []
    for i in range(101):
        t = i / 100
        x = 470 + (W - 470) * t
        y = 1350 - (40 + 200 * (1 - math.cos(t * math.pi)) / 2 + 35 * math.sin(t * math.pi))
        pts.append((P(x), P(y)))
    pts += [(P(W), P(H)), (P(470), P(H))]
    d.polygon(pts, fill=BLUE + (255,))
    # lighter inner band
    pts2 = [(x, y + P(26)) for x, y in pts[:101]] + [(P(W), P(H)), (P(470), P(H))]
    d.polygon(pts2, fill=(58, 172, 228, 255))
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    f = SEMI(19)
    lines = tagline.split("\n")
    for i, ln in enumerate(lines):
        tw = spaced_len(ln, f, 0.24)
        spaced(d, (P(W - 46) - tw, P(1238 + i * 34 - (len(lines) - 1) * 17)), ln, f, WHITE, 0.24)
    lw = P(62); x0 = P(W - 46) - spaced_len(lines[-1], f, .24) / 2 - lw / 2
    d.rectangle((x0, P(1290), x0 + lw, P(1293)), fill=WHITE)

def script_note(im, text, xy=(860, 70), size=44, angle=-9):
    lines = text.split("\n"); f = SCRIPT(size)
    wmax = max(f.getlength(l) for l in lines) + P(30)
    lay = Image.new("RGBA", (int(wmax), P(size * 1.15 * len(lines) + 30)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i, l in enumerate(lines):
        d.text((P(10) + i * P(14), P(4) + i * P(size * 1.1)), l, font=f, fill=(52, 58, 66))
    y_ul = P(10 + size * 1.1 * len(lines))
    d.line([(P(10), y_ul), (P(10) + f.getlength(lines[-1]) * .6, y_ul - P(6))], fill=(52, 58, 66), width=P(2))
    lay = lay.rotate(-angle * -1, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(lay, (P(xy[0]), P(xy[1])))

def render(name, cfg):
    im = base(); d = ImageDraw.Draw(im)
    L = 58; colw = cfg.get("colw", 600)
    # eyebrow
    f = SEMI(18); x = spaced(d, (P(L), P(60)), cfg.get("eyebrow", "LOCAL PEOPLE. STRONGER BUSINESSES."), f, (60, 66, 74), 0.3)
    d.line([(x + P(22), P(72)), (x + P(130), P(72))], fill=(60, 66, 74), width=P(2))
    # headline: fit every line to colw, cap size
    lines = cfg["head"]; size = cfg.get("hsize", 138)
    while size > 50 and (max(HEAD(size).getlength(t) for t, _ in lines) > P(cfg.get("hw", colw)) or
                         size * 0.93 * len(lines) > cfg.get("hmax", 470)):
        size -= 2
    hf = HEAD(size)
    rows = cfg["rows"]; rh = cfg.get("rh", 76 if len(rows) <= 4 else 66)
    nsub = len(wrap(cfg["sub"], BODY(31), P(colw)))
    nb = len(wrap(cfg["bottom"], BODY(25), P(colw - 150)))
    y_end = 108 + size * .93 * len(lines) + 18 + 42 * nsub + 44 + rh * len(rows) + 18 + 62 + 34 * nb
    extra = max(0, 1170 - y_end)
    add_rh = min(extra * .6 / len(rows), 96 - rh); rh += add_rh; extra -= add_rh * len(rows)
    gap = min(extra / 3, 26)
    y = 108
    for t, c in lines:
        bb = hf.getbbox(t)
        d.text((P(L) - bb[0], P(y) - bb[1]), t, font=hf, fill=c)
        y += size * 0.93
    y += 18 + gap
    # subhead
    sf = BODY(31)
    for ln in wrap(cfg["sub"], sf, P(colw)):
        d.text((P(L), P(y)), ln, font=sf, fill=TEXT); y += 42
    y += 14 + gap / 2; d.rectangle((P(L), P(y), P(L + 74), P(y + 4)), fill=BLUE); y += 30 + gap / 2
    rf = BODY(27 if len(rows) <= 4 else 25)
    for i, (k, txt) in enumerate(rows):
        cy = y + rh / 2
        d.ellipse((P(L), P(cy - 30), P(L + 60), P(cy + 30)), fill=BLUE_L)
        icon(d, k, L + 30, cy, 17)
        d.text((P(L + 92), P(cy) - rf.getbbox(txt)[3] / 2 - P(1)), txt, font=rf, fill=INK)
        if i < len(rows) - 1:
            d.line([(P(L), P(y + rh)), (P(L + colw - 10), P(y + rh))], fill=LINE, width=P(1.5))
        y += rh
    # bottom-line box
    y += 18 + gap; bx1 = L + colw + 10
    bf = BODY(25); blines = wrap(cfg["bottom"], bf, P(colw - 150)); bh = 62 + 34 * len(blines)
    d.rounded_rectangle((P(L), P(y), P(bx1), P(y + bh)), radius=P(14), fill=(233, 240, 246))
    icon(d, "bulb", L + 50, y + bh / 2, 22)
    for a in (-60, -20, 20, 60, 180, 0):
        pass
    d.line([(P(L + 98), P(y + 18)), (P(L + 98), P(y + bh - 18))], fill=(150, 160, 172), width=P(2))
    spaced(d, (P(L + 122), P(y + 18)), "THE BOTTOM LINE:", SEMI(15), (70, 78, 88), 0.2)
    for i, ln in enumerate(blines):
        d.text((P(L + 122), P(y + 44 + i * 34)), ln, font=bf, fill=INK)
    # visual + script note + footer
    cfg["visual"](im)
    if cfg.get("note"): script_note(im, cfg["note"], cfg.get("note_xy", (800, 52)))
    wave(im, cfg.get("wave", "QUALITY FIRST.\nRESULTS THAT MATTER."))
    lg = LOGO.resize((P(300), int(P(300) * LOGO.height / LOGO.width)), Image.LANCZOS)
    im.alpha_composite(lg, (P(L), P(H - 52) - lg.height))
    if cfg.get("howie"):
        hw = cfg["howie"]; hi = Image.open(os.path.join(HERE, "howie", "howie-%s.png" % hw.get("pose", "wave"))).convert("RGBA")
        hh = P(hw.get("h", 215)); hi = hi.resize((int(hi.width * hh / hi.height), hh), Image.LANCZOS)
        cx, fy = P(hw.get("x", 985)), P(hw.get("feet", 1110))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((cx - hi.width * .36, fy - P(10), cx + hi.width * .36, fy + P(10)), fill=(10, 31, 68, 90))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(P(6))))
        im.alpha_composite(hi, (int(cx - hi.width / 2), int(fy - hi.height)))
    out = im.convert("RGB").resize((W, H), Image.LANCZOS)
    out.save(f"{OUT}/{name}.png", optimize=True)
    return f"{OUT}/{name}.png"

# ---------- right-column visuals (region roughly x 690–1050, y 170–1000) ----------
def card(im, box, radius=28, fill=WHITE, sh=True):
    x0, y0, x1, y1 = box
    if sh: shadow(im, lambda d, c: d.rounded_rectangle((P(x0), P(y0), P(x1), P(y1)), radius=P(radius), fill=c))
    ImageDraw.Draw(im).rounded_rectangle((P(x0), P(y0), P(x1), P(y1)), radius=P(radius), fill=fill)

def people_cluster(d, cx, cy, n=11, spread=170, seed=3, col=(196, 203, 212)):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x = cx + rng.uniform(-spread, spread); y = cy + rng.uniform(-spread * .45, spread * .45); r = rng.uniform(16, 26)
        icon(d, "person", x, y, r, col)

def v_bars(im):
    d = ImageDraw.Draw(im)
    people_cluster(d, 880, 250, 9, 150)
    base_y = 860; hs = [470, 380, 300, 220]; labels = "ABCD"
    for i, h_ in enumerate(hs):
        x0 = 690 + i * 92; x1 = x0 + 66
        shadow(im, lambda dd, c, x0=x0, x1=x1, h_=h_: dd.rounded_rectangle((P(x0), P(base_y - h_), P(x1), P(base_y)), radius=P(10), fill=c), blur=16, alpha=50)
        g = vgrad(P(66), P(h_), (88, 190, 240), BLUE_D)
        m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.width - 1, g.height - 1), radius=P(10), fill=255)
        im.paste(g, (P(x0), P(base_y - h_)), m)
        d = ImageDraw.Draw(im)
        f = OUTF(40); tw = f.getlength(labels[i])
        d.text((P(x0 + 33) - tw / 2, P(base_y - h_ + 14)), labels[i], font=f, fill=WHITE)
        f2 = HEAD(54); tw = f2.getlength("?")
        d.text((P(x0 + 33) - tw / 2, P(base_y - h_ - 72)), "?", font=f2, fill=(150, 160, 172))
    d.rounded_rectangle((P(670), P(base_y), P(1060), P(base_y + 8)), radius=P(4), fill=(205, 214, 222))

def v_profile(im):
    card(im, (690, 200, 1040, 860))
    d = ImageDraw.Draw(im)
    g = vgrad(P(350), P(170), (120, 200, 240), BLUE)
    m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.width - 1, g.height + 40), radius=P(28), fill=255)
    im.paste(g, (P(690), P(200)), m); d = ImageDraw.Draw(im)
    d.ellipse((P(820), P(300), P(910), P(390)), fill=WHITE); icon(d, "pin", 865, 345, 30, BLUE)
    d.text((P(718), P(410)), "Your Business", font=OUTF(34), fill=INK)
    for k in range(5): icon(d, "star", 735 + k * 40, 486, 17, GOLD)
    d.text((P(940), P(472)), "5.0", font=OUTF(26), fill=TEXT)
    d.rounded_rectangle((P(718), P(530), P(860), P(570)), radius=P(20), fill=(220, 244, 230))
    d.text((P(736), P(536)), "Open now", font=SEMI(20), fill=GREEN)
    for i, w_ in enumerate((280, 230, 260, 190)):
        d.rounded_rectangle((P(718), P(610 + i * 40), P(718 + w_), P(626 + i * 40)), radius=P(8), fill=(228, 233, 238))
    for i, k in enumerate(("phone", "pin", "chat")):
        cx = 760 + i * 100
        d.ellipse((P(cx - 30), P(790 - 30), P(cx + 30), P(790 + 30)), fill=BLUE_L); icon(d, k, cx, 790, 17)

def v_speakers(im):
    d = ImageDraw.Draw(im)
    for i, (ini, nm) in enumerate((("ML", "Michael"), ("AS", "Abhishek"))):
        cx, cy, r = 870, 330 + i * 330, 125
        shadow(im, lambda dd, c, cx=cx, cy=cy: dd.ellipse((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), fill=c))
        d = ImageDraw.Draw(im)
        d.ellipse((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), fill=BLUE)
        d.ellipse((P(cx - r + 10), P(cy - r + 10), P(cx + r - 10), P(cy + r - 10)), fill=(225, 238, 247))
        f = HEAD(110); tw = f.getlength(ini); bb = f.getbbox(ini)
        d.text((P(cx) - tw / 2, P(cy) - (bb[1] + bb[3]) / 2), ini, font=f, fill=BLUE)
        lab = nm.upper(); f2 = SEMI(20); tw = spaced_len(lab, f2, .25)
        d.rounded_rectangle((P(cx) - tw / 2 - P(22), P(cy + r - 8), P(cx) + tw / 2 + P(22), P(cy + r + 38)), radius=P(10), fill=BLUE)
        spaced(d, (P(cx) - tw / 2, P(cy + r + 2)), lab, f2, WHITE, .25)

def v_fifty(im):
    d = ImageDraw.Draw(im)
    people_cluster(d, 870, 300, 16, 170, seed=5)
    f = HEAD(300); t = "50+"; tw = f.getlength(t)
    d.text((P(875) - tw / 2, P(420)), t, font=f, fill=BLUE)
    f2 = SEMI(22); lab = "LOCAL CLIENTS"; tw = spaced_len(lab, f2, .3)
    spaced(d, (P(875) - tw / 2, P(800)), lab, f2, INK, .3)
    d.rounded_rectangle((P(735), P(860), P(1015), P(930)), radius=P(14), fill=BLUE)
    lab = "ACROSS SIOUXLAND"; f3 = SEMI(20); tw = spaced_len(lab, f3, .25)
    spaced(d, (P(875) - tw / 2, P(880)), lab, f3, WHITE, .25)

def v_week(im):
    card(im, (700, 220, 1040, 830))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(700), P(220), P(1040), P(310)), radius=P(28), fill=BLUE); d.rectangle((P(700), P(280), P(1040), P(310)), fill=BLUE)
    spaced(d, (P(740), P(248)), "THIS WEEK", SEMI(26), WHITE, .3)
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]; on = {0, 2, 4}
    for i, dd in enumerate(days):
        y = 335 + i * 68
        d.text((P(732), P(y + 8)), dd, font=OUTF(26), fill=INK if i in on else (160, 168, 178))
        if i in on:
            d.rounded_rectangle((P(830), P(y), P(1010), P(y + 50)), radius=P(12), fill=BLUE_L)
            d.ellipse((P(842), P(y + 7), P(878), P(y + 43)), fill=BLUE); icon(d, "check", 860, y + 25, 12, WHITE)
            d.rounded_rectangle((P(892), P(y + 19), P(990), P(y + 31)), radius=P(6), fill=(150, 200, 230))
        else:
            d.rounded_rectangle((P(830), P(y + 19), P(960), P(y + 31)), radius=P(6), fill=(232, 236, 240))

def v_plan(im):
    card(im, (705, 230, 1040, 880), radius=22)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(810), P(198), P(935), P(258)), radius=P(14), fill=(60, 70, 82))
    d.ellipse((P(860), P(208), P(885), P(233)), fill=(238, 243, 247))
    t = "30-DAY"; f = HEAD(70); tw = f.getlength(t); d.text((P(872) - tw / 2, P(282)), t, font=f, fill=BLUE)
    t = "AI ACTION PLAN"; f2 = SEMI(21); tw = spaced_len(t, f2, .22); spaced(d, (P(872) - tw / 2, P(372)), t, f2, INK, .22)
    for i in range(6):
        y = 430 + i * 72; done = i < 3
        d.rounded_rectangle((P(735), P(y), P(775), P(y + 40)), radius=P(8), fill=BLUE if done else WHITE, outline=BLUE, width=P(3))
        if done: icon(d, "check", 755, y + 20, 13, WHITE)
        d.rounded_rectangle((P(795), P(y + 13), P(795 + (200 if i % 2 else 170)), P(y + 27)), radius=P(7), fill=(222, 229, 236))

def v_phone(im):
    shadow(im, lambda d, c: d.rounded_rectangle((P(740), P(190), P(1010), P(740)), radius=P(44), fill=c))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(740), P(190), P(1010), P(740)), radius=P(44), fill=(30, 36, 44))
    d.rounded_rectangle((P(754), P(204), P(996), P(726)), radius=P(34), fill=(246, 249, 252))
    d.rounded_rectangle((P(838), P(214), P(912), P(232)), radius=P(9), fill=(30, 36, 44))
    d.ellipse((P(825), P(280), P(925), P(380)), fill=(253, 228, 228)); icon(d, "phone", 875, 330, 30, RED)
    t = "Missed call"; f = OUTF(30); tw = f.getlength(t); d.text((P(875) - tw / 2, P(400)), t, font=f, fill=RED)
    t = "2:14 PM"; f = BODY(22); tw = f.getlength(t); d.text((P(875) - tw / 2, P(444)), t, font=f, fill=MUTED)
    # text bubble overlapping the phone
    shadow(im, lambda dd, c: dd.rounded_rectangle((P(640), P(560), P(1000), P(720)), radius=P(26), fill=c), blur=20, alpha=70)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(640), P(560), P(1000), P(720)), radius=P(26), fill=BLUE)
    d.polygon([(P(960), P(700)), (P(1010), P(745)), (P(930), P(716))], fill=BLUE)
    f = SEMI(24)
    for i, ln in enumerate(["Hi! Sorry we missed you.", "How can we help today?"]):
        d.text((P(666), P(590 + i * 36)), ln, font=f, fill=WHITE)
    d.text((P(666), P(670)), "Sent automatically", font=BODY(18), fill=(214, 238, 250))
    d.rounded_rectangle((P(700), P(790), P(1040), P(860)), radius=P(35), fill=WHITE, outline=BLUE, width=P(3))
    icon(d, "check", 740, 825, 16, GREEN)
    d.text((P(770), P(808)), "Lead saved to CRM", font=SEMI(24), fill=INK)

def v_steps(im):
    d = ImageDraw.Draw(im)
    base_y = 880
    for i in range(3):
        x0 = 690 + i * 118; h_ = 170 + i * 150
        shadow(im, lambda dd, c, x0=x0, h_=h_: dd.rounded_rectangle((P(x0), P(base_y - h_), P(x0 + 104), P(base_y)), radius=P(12), fill=c), blur=14, alpha=55)
        g = vgrad(P(104), P(h_), (96, 194, 240), BLUE_D)
        m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.width - 1, g.height - 1), radius=P(12), fill=255)
        im.paste(g, (P(x0), P(base_y - h_)), m)
        d = ImageDraw.Draw(im); f = HEAD(96); t = str(i + 1); tw = f.getlength(t)
        d.text((P(x0 + 52) - tw / 2, P(base_y - h_ + 12)), t, font=f, fill=WHITE)
    icon(d, "person", 1002, base_y - 470 - 70, 46, INK)
    d.rounded_rectangle((P(680), P(base_y), P(1050), P(base_y + 10)), radius=P(5), fill=(205, 214, 222))
    lab = "BUILD THE FOUNDATION FIRST"; f2 = SEMI(17); tw = spaced_len(lab, f2, .25)
    spaced(d, (P(865) - tw / 2, P(base_y + 30)), lab, f2, MUTED, .25)

def v_chat(im):
    d = ImageDraw.Draw(im)
    people_cluster(d, 870, 230, 7, 140, seed=9)
    shadow(im, lambda dd, c: dd.rounded_rectangle((P(700), P(330), P(1040), P(640)), radius=P(40), fill=c))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(700), P(330), P(1040), P(640)), radius=P(40), fill=BLUE)
    d.polygon([(P(760), P(620)), (P(840), P(620)), (P(730), P(710))], fill=BLUE)
    f = HEAD(230); tw = f.getlength("?"); d.text((P(870) - tw / 2, P(345)), "?", font=f, fill=WHITE)
    for i, (t, x, y) in enumerate((("ChatGPT", 720, 740), ("Claude", 880, 790), ("Gemini", 700, 850), ("Perplexity", 850, 905))):
        f = SEMI(24); w_ = f.getlength(t) + P(40)
        shadow(im, lambda dd, c, x=x, y=y, w_=w_: dd.rounded_rectangle((P(x), P(y), P(x) + w_, P(y + 48)), radius=P(24), fill=c), blur=10, alpha=40)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((P(x), P(y), P(x) + w_, P(y + 48)), radius=P(24), fill=WHITE, outline=(200, 225, 240), width=P(2))
        d.text((P(x + 20), P(y + 9)), t, font=f, fill=INK)

def v_calendar(top="NOV", big="12", sub="THURSDAY", ribbon="THIS WEEK"):
    def draw(im):
        card(im, (705, 240, 1040, 720), radius=30)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((P(705), P(240), P(1040), P(360)), radius=P(30), fill=BLUE); d.rectangle((P(705), P(320), P(1040), P(360)), fill=BLUE)
        for x in (790, 955):
            d.rounded_rectangle((P(x - 10), P(212), P(x + 10), P(272)), radius=P(10), fill=(60, 70, 82))
        f = SEMI(40); tw = spaced_len(top, f, .3); spaced(d, (P(872) - tw / 2, P(280)), top, f, WHITE, .3)
        f = HEAD(250); tw = f.getlength(big); d.text((P(872) - tw / 2, P(355)), big, font=f, fill=INK)
        f = SEMI(26); tw = spaced_len(sub, f, .3); spaced(d, (P(872) - tw / 2, P(650)), sub, f, MUTED, .3)
        if ribbon:
            shadow(im, lambda dd, c: dd.rounded_rectangle((P(680), P(770), P(1060), P(850)), radius=P(16), fill=c), blur=14, alpha=55)
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((P(680), P(770), P(1060), P(850)), radius=P(16), fill=INK)
            f = HEAD(52); tw = f.getlength(ribbon); d.text((P(870) - tw / 2, P(780)), ribbon, font=f, fill=WHITE)
    return draw

def v_mug(im):
    v_calendar("NOV", "12", "THURSDAY", None)(im)
    mug_dy = 120
    # coffee mug in front, echoing the reference
    shadow(im, lambda d, c: d.rounded_rectangle((P(700), P(640 + mug_dy), P(920), P(900 + mug_dy)), radius=P(26), fill=c))
    d = ImageDraw.Draw(im)
    d.ellipse((P(880), P(690 + mug_dy), P(970), P(820 + mug_dy)), outline=(236, 240, 244), width=P(18))
    d.rounded_rectangle((P(700), P(640 + mug_dy), P(920), P(900 + mug_dy)), radius=P(26), fill=WHITE)
    d.ellipse((P(700), P(625 + mug_dy), P(920), P(660 + mug_dy)), fill=(232, 236, 240)); d.ellipse((P(712), P(630 + mug_dy), P(908), P(655 + mug_dy)), fill=(120, 80, 50))
    f = SCRIPT(34)
    for i, t in enumerate(["Learn it.", "See it.", "Use it."]):
        d.text((P(732 + i * 8), P(690 + mug_dy + i * 54)), t, font=f, fill=(52, 58, 66))

SUMMIT = "NW IOWA AI BUSINESS SUMMIT · NOV 12"
G = {
"02-poll-leads": dict(head=[("WHERE DO YOUR", BLUE), ("BEST CUSTOMERS", INK), ("COME FROM?", BLUE)],
    sub="Your answer should decide where your next marketing dollar goes.",
    rows=[("A", "Google search"), ("B", "Word of mouth"), ("C", "Social media"), ("D", "Something else")],
    bottom="Spend more where your best customers already find you.", note="Tell us\nbelow!", visual=v_bars,
    wave="COMMENT YOUR LETTER.\nWE'LL SHARE THE RESULTS."),
"03-gbp-checklist": dict(head=[("5-MINUTE", BLUE), ("GOOGLE PROFILE", INK), ("TUNE-UP.", BLUE)],
    sub="It's often the first thing customers see, before your website.",
    rows=[("1", "Update your hours (holidays!)"), ("2", "Add 3 fresh photos"), ("3", "Reply to recent reviews"), ("4", "Check your services list"), ("5", "Publish an update post")],
    bottom="A current profile keeps you showing up in Maps and “near me” searches.", note="Small effort,\nreal visibility", visual=v_profile,
    wave="SAVE THIS.\nSHARE IT WITH A FRIEND."),
"04-speakers": dict(eyebrow=SUMMIT, head=[("MEET YOUR", INK), ("SPEAKERS.", BLUE)],
    sub="Real tools, live demos, and straight answers to your questions.",
    rows=[("person", "Michael Lewis · Owner, Lewis Marketing"), ("person", "Abhishek Shastry · Senior Web Developer"), ("calendar", "Thu, Nov 12 · Doors 8:30 AM"), ("pin", "Northwestern College, Orange City")],
    bottom="Drop your AI question in the comments. We'll build it into the day.", note="Bring your\nquestions!", visual=v_speakers,
    wave="LEARN IT. SEE IT.\nUSE IT."),
"06-trusted": dict(eyebrow="THANK YOU, SIOUXLAND.", head=[("NO TWO", BLUE), ("BUSINESSES GET", INK), ("THE SAME PLAN.", INK)],
    sub="Plumbers, banks, steakhouses, churches. Every plan starts with your goals.",
    rows=[("pin", "50+ businesses across Siouxland"), ("chart", "Built around your goals and budget"), ("check", "Websites, ads, CRM and content"), ("star", "Measured in leads and customers")],
    bottom="Thank you to every client who trusts us with their name.", note="Grateful\nfor you", visual=v_fifty,
    wave="LOCAL PEOPLE.\nSTRONGER BUSINESSES."),
"07-myth": dict(head=[("POSTING DAILY", BLUE), ("ISN'T THE GOAL.", INK), ("CONSISTENCY", BLUE), ("> VOLUME.", INK)],
    sub="Three helpful posts a week beat seven rushed ones.",
    rows=[("calendar", "A schedule your audience can count on"), ("bulb", "Posts that teach or answer a question"), ("chat", "Real replies to every comment"), ("chart", "Results you can actually measure")],
    bottom="Volume without strategy is just noise.", note="Quality over\nquantity", visual=v_week,
    wave="AGREE OR DISAGREE?\nTELL US BELOW."),
"08-takeaways": dict(eyebrow=SUMMIT, head=[("DON'T JUST", INK), ("LEARN AI.", BLUE), ("LEAVE WITH", INK), ("A PLAN.", BLUE)],
    sub="One day. Four AI tools. A plan you'll use the next morning.",
    rows=[("check", "Your 30-Day AI Action Plan"), ("check", "ChatGPT, Claude, Gemini & Perplexity"), ("check", "Prompts to use the next morning"), ("check", "Lunch + local connections")],
    bottom="Thu, Nov 12 · Northwestern College, Orange City · $49.99", note="Learn it.\nSee it. Use it.", visual=v_plan,
    wave="REGISTER TODAY.\nLINK IN BIO."),
"10-speed-to-lead": dict(head=[("MISSED CALL?", BLUE), ("THEY'RE ALREADY", INK), ("CALLING SOMEONE", INK), ("ELSE.", BLUE)],
    sub="A missed-call text-back keeps the conversation going.",
    rows=[("phone", "A call goes unanswered"), ("chat", "They get an instant text"), ("person", "The lead stays with you"), ("chart", "Everything's tracked in your CRM")],
    bottom="Fast follow-up turns missed calls into booked jobs.", note="Never miss\na lead", visual=v_phone,
    wave="SPEED TO LEAD\nWINS THE JOB."),
"11-free-class": dict(head=[("BEFORE YOU", INK), ("SPEND ANOTHER", INK), ("DOLLAR ON ADS…", BLUE)],
    sub="Free class: 3 Essentials Before Marketing.",
    rows=[("bulb", "Learn what to fix first"), ("chart", "Stop wasting ad spend"), ("check", "No sales pitch"), ("calendar", "Free to attend")],
    bottom="Strong foundations make every marketing dollar work harder.", note="Start\nhere", visual=v_steps,
    wave="REGISTER FREE AT\nLEWISMARKETINGOC.COM"),
"13-ai-poll": dict(head=[("WHICH AI TOOL", BLUE), ("DO YOU USE", INK), ("MOST?", BLUE)],
    sub="We're covering all four at Thursday's AI Business Summit.",
    rows=[("1", "ChatGPT"), ("2", "Claude"), ("3", "Gemini"), ("4", "Perplexity"), ("5", "None yet (no judgment!)")],
    bottom="Comment your number and tell us what you use it for.", note="No wrong\nanswers", visual=v_chat,
    wave="COMMENT YOUR\nNUMBER BELOW."),
"14-last-call": dict(eyebrow=SUMMIT, head=[("LAST CALL.", BLUE), ("THE SUMMIT IS", INK), ("THIS THURSDAY.", INK)],
    sub="One day of practical AI for business owners, lunch included.",
    rows=[("calendar", "Thu, Nov 12 · Doors 8:30 AM"), ("pin", "Northwestern College, Orange City"), ("check", "Leave with a 30-Day AI Action Plan"), ("star", "$49.99 · lunch included")],
    bottom="If AI is on your “someday” list, make it this month.", note="Save your\nseat!", visual=v_calendar(),
    wave="REGISTER TODAY.\nLINK IN BIO."),
"15-today": dict(eyebrow=SUMMIT, head=[("IT'S", INK), ("SUMMIT DAY!", BLUE)],
    sub="Doors open at 8:30 AM, and the coffee's on.",
    rows=[("pin", "Vogel Room, DeWitt Learning Commons"), ("pin", "Northwestern College, Orange City"), ("clock", "Check-in 8:30 · Sessions 9:00"), ("chat", "Follow our Stories all day")],
    bottom="Thank you to the Center for Innovation & Leadership at Northwestern College.", note="See you\nsoon!", visual=v_mug,
    wave="LEARN IT. SEE IT.\nUSE IT."),
}

if __name__ == "__main__":
    import sys
    for k in (sys.argv[1:] or G):
        print(render(k, G[k]))
