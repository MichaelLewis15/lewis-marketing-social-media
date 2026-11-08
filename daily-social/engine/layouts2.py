"""Ten more Lewis Marketing feed layouts (1080x1350). Importing this module registers them in layouts.LAYOUTS.

  checklist : white clipboard page on blue, ticked boxes.                      (checklists, audits, "before you...")
  versus    : DON'T vs DO columns; uses "dont" and "do" lists (falls back to rows). (mistakes vs fixes)
  stat      : one huge stat on sunshine yellow; uses "big" (e.g. "46%") and "source". (sourced stats only)
  phone     : phone mockup with a message bubble; uses "message" (+ "from").   (texting, missed calls, reviews, DMs)
  steps     : vertical roadmap with numbered stops.                             (processes, 3-5 step how-tos)
  poll      : This or That, two option cards; uses "a" and "b" (+ "ask").      (engagement polls)
  bold      : giant typographic headline with highlight blocks, minimal.        (hot takes, one-liners)
  browser   : website mockup in a browser window; uses "url".                   (website, SEO, landing pages)
  question  : huge question mark, question headline, comment box.              (open questions, community)
  calendar  : tear-off calendar page; uses "month" and "day" (+ "weekday").     (deadlines, seasonal, countdowns)
Shared fields: eyebrow, head [[text, "ink"|"blue"]], sub, rows [[n, text]], bottom, howie.
"""
from PIL import Image, ImageDraw, ImageFilter
import graphics2 as g
from graphics2 import P, W, H, BLUE, BLUE_D, BLUE_L, INK, TEXT, MUTED, LINE, WHITE, RED, GREEN, HEAD, BODY, SEMI, OUTF, SCRIPT, wrap
import layouts as L0
from layouts import canvas, radial, dots, logo, howie, fit_head, draw_head, pill, finish, NAVY, NAVY2, SUN, MIST, SKY

CREAM = (255, 251, 240)


def rows_of(s, k=5): return [t for _, t in s.get("rows", [])[:k]]


def text_block(d, text, font, x, y, maxw, fill, lh=1.3, maxl=3, center=False):
    for ln in wrap(text, font, P(maxw))[:maxl]:
        xx = P(x) - font.getlength(ln) / 2 if center else P(x)
        d.text((xx, P(y)), ln, font=font, fill=fill); y += font.size / P(1) * lh
    return y


# ---------------------------------------------------------------- checklist
def l_checklist(s, path):
    im = canvas(SKY); dots(im, (255, 255, 255), 30); radial(im, 540, 200, 500, (255, 255, 255), 40)
    d = ImageDraw.Draw(im)
    g.card(im, (80, 150, 1000, 1180), radius=22, fill=WHITE); d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(380), P(110), P(700), P(190)), radius=P(18), fill=NAVY)
    d.ellipse((P(520), P(122), P(560), P(162)), fill=SKY)
    y = 230; x = 140
    pill(d, x, y, s.get("eyebrow", "CHECKLIST"), BLUE_L, BLUE_D, 18); y += 70
    size = fit_head(s["head"], 800, 260, 110)
    y = draw_head(d, s["head"], x, y, size, {"ink": INK, "blue": SKY}) + 16
    y = text_block(d, s.get("sub", ""), BODY(32), x, y, 800, TEXT, 1.35, 2) + 24
    items = rows_of(s, 5); rh = min(118, (1060 - y) / max(len(items), 1))
    for t in items:
        d.rounded_rectangle((P(x), P(y + 6), P(x + 54), P(y + 60)), radius=P(10), outline=SKY, width=P(5))
        g.icon(d, "check", x + 28, y + 32, 24, GREEN)
        yy = y + 8
        for ln in wrap(t, SEMI(34), P(700))[:2]: d.text((P(x + 84), P(yy)), ln, font=SEMI(34), fill=INK); yy += 44
        d.line([(P(x), P(y + rh - 12)), (P(940), P(y + rh - 12))], fill=LINE, width=P(2)); y += rh
    if s.get("bottom"): text_block(d, s["bottom"].upper(), HEAD(40), x, 1100, 700, BLUE_D, 1.0, 1)
    logo(im, True, 80, None, 250)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 965, "feet": 1320, "h": 230})
    return finish(im, path)


# ---------------------------------------------------------------- versus
def l_versus(s, path):
    im = canvas(MIST); d = ImageDraw.Draw(im); L = 60
    pill(d, L, 60, s.get("eyebrow", "DO THIS, NOT THAT"), NAVY, WHITE, 20)
    size = fit_head(s["head"], 960, 250, 120)
    y = draw_head(d, s["head"], L, 140, size, {"ink": INK, "blue": SKY}) + 30
    dont = s.get("dont") or rows_of(s, 4)[:2]; do = s.get("do") or rows_of(s, 4)[2:]
    top = y; bot = 1150; cw = (W - 2 * L - 30) / 2
    for i, (lab, items, col, bg, ic) in enumerate([("DON'T", dont, RED, (253, 236, 236), "x"), ("DO", do, GREEN, (232, 247, 238), "check")]):
        x0 = L + i * (cw + 30)
        g.card(im, (x0, top, x0 + cw, bot), radius=24, fill=WHITE); d = ImageDraw.Draw(im)
        d.rounded_rectangle((P(x0), P(top), P(x0 + cw), P(top + 110)), radius=P(24), fill=bg)
        d.rectangle((P(x0), P(top + 60), P(x0 + cw), P(top + 110)), fill=bg)
        d.ellipse((P(x0 + 30), P(top + 25), P(x0 + 90), P(top + 85)), fill=col)
        g.icon(d, ic, x0 + 60, top + 55, 20, WHITE)
        d.text((P(x0 + 108), P(top + 22)), lab, font=HEAD(64), fill=col)
        yy = top + 150
        for t in items[:4]:
            d.ellipse((P(x0 + 34), P(yy + 14), P(x0 + 48), P(yy + 28)), fill=col)
            ls = wrap(t, SEMI(38), P(cw - 100))[:3]
            for ln in ls: d.text((P(x0 + 66), P(yy - 2)), ln, font=SEMI(38), fill=INK); yy += 50
            yy += 50
    logo(im, False, L, None, 250)
    howie(im, s.get("howie"), {"pose": "idle", "x": 960, "feet": 1320, "h": 200})
    return finish(im, path)


# ---------------------------------------------------------------- stat
def l_stat(s, path):
    im = canvas(SUN); radial(im, 820, 300, 520, (255, 230, 140), 200); d = ImageDraw.Draw(im); L = 70
    pill(d, L, 70, s.get("eyebrow", "BY THE NUMBERS"), NAVY, WHITE, 20)
    big = str(s.get("big", "?")); size = 420
    while HEAD(size).getlength(big) > P(940) and size > 120: size -= 10
    bf = HEAD(size); bb = bf.getbbox(big)
    d.text((P(L) - bb[0], P(150) - bb[1]), big, font=bf, fill=NAVY)
    y = 150 + (bb[3] - bb[1]) / P(1) + 40
    hs = fit_head(s["head"], 940, 240, 92)
    y = draw_head(d, s["head"], L, y, hs, {"ink": NAVY, "blue": (196, 54, 54)}) + 20
    y = text_block(d, s.get("sub", ""), BODY(34, 600), L, y, 880, NAVY, 1.35, 3) + 20
    for t in rows_of(s, 3):
        d.rectangle((P(L), P(y + 12), P(L + 26), P(y + 18)), fill=NAVY)
        y = text_block(d, t, SEMI(32), L + 44, y, 800, NAVY, 1.3, 2) + 10
    if s.get("source"): d.text((P(L), P(1172)), "Source: " + s["source"], font=BODY(24, 600), fill=(90, 70, 20))
    d.rectangle((0, P(H - 110), P(W), P(H)), fill=NAVY)
    logo(im, True, L, H - 90, 240)
    howie(im, s.get("howie"), {"pose": "cheer", "x": 940, "feet": H - 95, "h": 250})
    return finish(im, path)


# ---------------------------------------------------------------- phone
def l_phone(s, path):
    im = g.vgrad(P(W), P(H), (14, 44, 92), (24, 120, 176)); dots(im, (255, 255, 255), 16); d = ImageDraw.Draw(im); L = 64
    pill(d, L, 60, s.get("eyebrow", "QUICK FIX"), SUN, NAVY, 20)
    size = fit_head(s["head"], 520, 420, 108)
    y = draw_head(d, s["head"], L, 140, size, {"ink": WHITE, "blue": SUN}) + 20
    y = text_block(d, s.get("sub", ""), BODY(30), L, y, 500, (210, 226, 240), 1.35, 4) + 20
    for i, t in enumerate(rows_of(s, 4)):
        d.ellipse((P(L), P(y + 2), P(L + 46), P(y + 48)), fill=SUN)
        nb = HEAD(32).getbbox(str(i + 1)); d.text((P(L + 23) - (nb[0] + nb[2]) / 2, P(y + 25) - (nb[1] + nb[3]) / 2), str(i + 1), font=HEAD(32), fill=NAVY)
        yy = y + 4
        for ln in wrap(t, SEMI(33), P(470))[:2]: d.text((P(L + 64), P(yy)), ln, font=SEMI(33), fill=WHITE); yy += 42
        y = max(y + 74, yy + 22)
    # phone
    px, py, pw, ph = 620, 150, 400, 640
    g.shadow(im, lambda dd, c: dd.rounded_rectangle((P(px), P(py), P(px + pw), P(py + ph)), radius=P(56), fill=c), (0, 24), 30, 110)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(px), P(py), P(px + pw), P(py + ph)), radius=P(56), fill=(12, 16, 24))
    d.rounded_rectangle((P(px + 14), P(py + 14), P(px + pw - 14), P(py + ph - 14)), radius=P(44), fill=(244, 246, 250))
    d.rounded_rectangle((P(px + 150), P(py + 28), P(px + 250), P(py + 50)), radius=P(11), fill=(12, 16, 24))
    d.text((P(px + 40), P(py + 76)), s.get("from", "Lewis Marketing"), font=SEMI(24), fill=INK)
    d.text((P(px + 40), P(py + 108)), "Text message · now", font=BODY(19), fill=MUTED)
    d.line([(P(px + 30), P(py + 146)), (P(px + pw - 30), P(py + 146))], fill=LINE, width=P(2))
    msg = s.get("message", "Thanks for calling! How can we help?")
    f = BODY(26); ls = wrap(msg, f, P(pw - 130))[:8]; bh = len(ls) * 36 + 36
    by = py + 186
    d.rounded_rectangle((P(px + 36), P(by), P(px + pw - 56), P(by + bh)), radius=P(24), fill=SKY)
    yy = by + 18
    for ln in ls: d.text((P(px + 60), P(yy)), ln, font=f, fill=WHITE); yy += 36
    if s.get("reply"):
        ry = by + bh + 26; rl = wrap(s["reply"], f, P(pw - 150))[:3]; rh = len(rl) * 36 + 36
        d.rounded_rectangle((P(px + 90), P(ry), P(px + pw - 36), P(ry + rh)), radius=P(24), fill=(226, 230, 236))
        yy = ry + 18
        for ln in rl: d.text((P(px + 112), P(yy)), ln, font=f, fill=INK); yy += 36
    if s.get("bottom"): text_block(d, s["bottom"].upper(), HEAD(46), L, 1110, 760, SUN, 1.0, 2)
    logo(im, True, L, None, 250)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 960, "feet": 1320, "h": 230})
    return finish(im, path)


# ---------------------------------------------------------------- steps
def l_steps(s, path):
    im = canvas(WHITE); d = ImageDraw.Draw(im); L = 70
    d.rectangle((0, 0, P(W), P(14)), fill=SKY)
    pill(d, L, 60, s.get("eyebrow", "STEP BY STEP"), SKY, WHITE, 20)
    size = fit_head(s["head"], 940, 260, 120)
    y = draw_head(d, s["head"], L, 140, size, {"ink": NAVY, "blue": SKY}) + 14
    y = text_block(d, s.get("sub", ""), BODY(32), L, y, 900, TEXT, 1.35, 2) + 36
    items = rows_of(s, 5); n = len(items); gap = min(150, (1130 - y) / max(n, 1)); cx = L + 44
    d.line([(P(cx), P(y + 44)), (P(cx), P(y + 44 + gap * (n - 1)))], fill=BLUE_L, width=P(10))
    for i, t in enumerate(items):
        yy = y + i * gap
        d.ellipse((P(cx - 44), P(yy), P(cx + 44), P(yy + 88)), fill=NAVY if i == n - 1 else SKY)
        nb = HEAD(52).getbbox(str(i + 1)); d.text((P(cx) - (nb[0] + nb[2]) / 2, P(yy + 44) - (nb[1] + nb[3]) / 2), str(i + 1), font=HEAD(52), fill=WHITE)
        g.card(im, (cx + 74, yy + 4, 840, yy + 84), radius=18, fill=MIST, sh=False); d = ImageDraw.Draw(im)
        ls = wrap(t, SEMI(32), P(680))[:2]; ty = yy + 44 - len(ls) * 21
        for ln in ls: d.text((P(cx + 100), P(ty)), ln, font=SEMI(32), fill=INK); ty += 42
    if s.get("bottom"): text_block(d, s["bottom"], OUTF(36), L, 1160, 760, BLUE_D, 1.2, 1)
    d.rectangle((0, P(H - 14), P(W), P(H)), fill=NAVY)
    logo(im, False, W - 330, 40, 260)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 965, "feet": 1320, "h": 240})
    return finish(im, path)


# ---------------------------------------------------------------- poll
def l_poll(s, path):
    im = canvas(NAVY); radial(im, 540, 700, 600, SKY, 60); dots(im, (255, 255, 255), 18); d = ImageDraw.Draw(im)
    pill(d, W / 2, 60, s.get("eyebrow", "THIS OR THAT"), SUN, NAVY, 22, center=True)
    size = fit_head(s["head"], 940, 230, 110)
    y = draw_head(d, s["head"], W / 2, 150, size, {"ink": WHITE, "blue": SUN}, center=True) + 40
    top = y; cw = 440; ch = 470
    for i, (lab, txt, col) in enumerate([("A", s.get("a", "Option A"), SKY), ("B", s.get("b", "Option B"), SUN)]):
        x0 = 70 + i * (cw + 60)
        g.card(im, (x0, top, x0 + cw, top + ch), radius=30, fill=WHITE); d = ImageDraw.Draw(im)
        d.ellipse((P(x0 + cw / 2 - 70), P(top + 50), P(x0 + cw / 2 + 70), P(top + 190)), fill=col)
        lb = HEAD(110).getbbox(lab); d.text((P(x0 + cw / 2) - (lb[0] + lb[2]) / 2, P(top + 120) - (lb[1] + lb[3]) / 2), lab, font=HEAD(110), fill=NAVY if col == SUN else WHITE)
        f = OUTF(46); ls = wrap(txt, f, P(cw - 130))
        while len(ls) > 5 and f.size > P(26): f = OUTF(f.size / P(1) - 4); ls = wrap(txt, f, P(cw - 130))
        yy = top + 240
        for ln in ls[:6]: d.text((P(x0 + cw / 2) - f.getlength(ln) / 2, P(yy)), ln, font=f, fill=INK); yy += f.size / P(1) * 1.25
    vs = HEAD(90); d.ellipse((P(W / 2 - 58), P(top + ch / 2 - 58), P(W / 2 + 58), P(top + ch / 2 + 58)), fill=(196, 54, 54))
    vf = HEAD(58); vb = vf.getbbox("VS"); d.text((P(W / 2) - (vb[0] + vb[2]) / 2, P(top + ch / 2) - (vb[1] + vb[3]) / 2), "VS", font=vf, fill=WHITE)
    ask = s.get("ask", "Comment A or B")
    af = SEMI(36); d.text((P(W / 2) - af.getlength(ask) / 2, P(top + ch + 40)), ask, font=af, fill=WHITE)
    logo(im, True, 70, None, 250)
    howie(im, s.get("howie"), {"pose": "cheer", "x": 960, "feet": 1320, "h": 210})
    return finish(im, path)


# ---------------------------------------------------------------- bold
def l_bold(s, path):
    im = canvas(WHITE); d = ImageDraw.Draw(im); L = 64
    pill(d, L, 60, s.get("eyebrow", "HOT TAKE"), INK, WHITE, 20)
    lines = s["head"]; size = fit_head(lines, 950, 760, 230, .98)
    f = HEAD(size); y = 150
    for t, c in lines:
        bb = f.getbbox(t); w = bb[2] - bb[0]; h = bb[3] - bb[1]
        if c == "blue":
            d.rectangle((P(L) - P(10), P(y) + h * .08, P(L) + w + P(14), P(y) + h * 1.12), fill=SUN)
            d.text((P(L) - bb[0], P(y) - bb[1] + h * .1), t, font=f, fill=NAVY)
        else:
            d.text((P(L) - bb[0], P(y) - bb[1] + h * .1), t, font=f, fill=INK)
        y += size * .98
    y += 30
    d.rectangle((P(L), P(y), P(L + 120), P(y + 10)), fill=SKY); y += 40
    y = text_block(d, s.get("sub", ""), BODY(36), L, y, 760, TEXT, 1.35, 3) + 10
    if s.get("bottom"): text_block(d, s["bottom"], SEMI(32), L, y + 10, 760, BLUE_D, 1.3, 2)
    logo(im, False, L, None, 260)
    howie(im, s.get("howie"), {"pose": "idle", "x": 960, "feet": 1320, "h": 240})
    return finish(im, path)


# ---------------------------------------------------------------- browser
def l_browser(s, path):
    im = canvas(BLUE_L); radial(im, 900, 200, 500, (255, 255, 255), 160); d = ImageDraw.Draw(im); L = 60
    pill(d, L, 50, s.get("eyebrow", "WEBSITE TIP"), NAVY, WHITE, 20)
    bx0, by0, bx1, by1 = L, 120, W - L, 1150
    g.card(im, (bx0, by0, bx1, by1), radius=22, fill=WHITE); d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(bx0), P(by0), P(bx1), P(by0 + 74)), radius=P(22), fill=(232, 236, 242)); d.rectangle((P(bx0), P(by0 + 40), P(bx1), P(by0 + 74)), fill=(232, 236, 242))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]): d.ellipse((P(bx0 + 28 + i * 34), P(by0 + 26), P(bx0 + 50 + i * 34), P(by0 + 48)), fill=c)
    d.rounded_rectangle((P(bx0 + 150), P(by0 + 18), P(bx1 - 40), P(by0 + 56)), radius=P(19), fill=WHITE)
    d.text((P(bx0 + 176), P(by0 + 24)), s.get("url", "yourbusiness.com"), font=BODY(22, 600), fill=MUTED)
    x = bx0 + 56; y = by0 + 120
    size = fit_head(s["head"], 820, 300, 112)
    y = draw_head(d, s["head"], x, y, size, {"ink": INK, "blue": SKY}) + 16
    y = text_block(d, s.get("sub", ""), BODY(32), x, y, 820, TEXT, 1.35, 2) + 24
    d.rounded_rectangle((P(x), P(y), P(x + 300), P(y + 70)), radius=P(35), fill=SKY)
    btn = s.get("button", "Call now"); bf = SEMI(28); d.text((P(x + 150) - bf.getlength(btn) / 2, P(y + 17)), btn, font=bf, fill=WHITE)
    y += 110
    for t in rows_of(s, 4):
        g.icon(d, "check", x + 18, y + 22, 18, GREEN)
        yy = y
        for ln in wrap(t, SEMI(31), P(700))[:2]: d.text((P(x + 50), P(yy)), ln, font=SEMI(31), fill=INK); yy += 40
        y = yy + 22
    if s.get("bottom"): text_block(d, s["bottom"].upper(), HEAD(40), L, 1180, 700, NAVY, 1.0, 1)
    logo(im, False, W - 320, None, 250)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 930, "feet": 1130, "h": 210})
    return finish(im, path)


# ---------------------------------------------------------------- question
def l_question(s, path):
    im = canvas(SKY); d = ImageDraw.Draw(im)
    qf = HEAD(1300); qb = qf.getbbox("?")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).text((P(560) - qb[0], P(-60) - qb[1]), "?", font=qf, fill=(255, 255, 255, 38)); im.alpha_composite(lay)
    d = ImageDraw.Draw(im); L = 70
    pill(d, L, 70, s.get("eyebrow", "YOUR TURN"), WHITE, BLUE_D, 20)
    size = fit_head(s["head"], 900, 480, 140)
    y = draw_head(d, s["head"], L, 160, size, {"ink": WHITE, "blue": NAVY}) + 24
    y = text_block(d, s.get("sub", ""), BODY(36, 600), L, y, 880, WHITE, 1.35, 3) + 40
    for t in rows_of(s, 3):
        g.card(im, (L, y, L + 700, y + 76), radius=38, fill=(255, 255, 255), sh=False); d = ImageDraw.Draw(im)
        d.text((P(L + 34), P(y + 18)), t, font=SEMI(30), fill=INK); y += 96
    y = max(y + 10, 900)
    g.card(im, (L, y, W - 230, y + 110), radius=26, fill=WHITE); d = ImageDraw.Draw(im)
    g.icon(d, "chat", L + 60, y + 55, 26, SKY)
    d.text((P(L + 110), P(y + 34)), s.get("prompt", "Tell us in the comments..."), font=BODY(32), fill=MUTED)
    d.rectangle((P(W - 300), P(y + 30), P(W - 296), P(y + 80)), fill=SKY)
    logo(im, True, L, None, 250)
    howie(im, s.get("howie"), {"pose": "wave", "x": 965, "feet": 1320, "h": 250})
    return finish(im, path)


# ---------------------------------------------------------------- calendar
def l_calendar(s, path):
    im = canvas(CREAM); dots(im, (200, 180, 140), 22, 30); d = ImageDraw.Draw(im); L = 64
    cx0, cy0, cx1, cy1 = 600, 110, 1010, 590
    g.card(im, (cx0, cy0, cx1, cy1), radius=26, fill=WHITE); d = ImageDraw.Draw(im)
    d.rounded_rectangle((P(cx0), P(cy0), P(cx1), P(cy0 + 120)), radius=P(26), fill=(196, 54, 54)); d.rectangle((P(cx0), P(cy0 + 70), P(cx1), P(cy0 + 120)), fill=(196, 54, 54))
    for k in (cx0 + 110, cx1 - 110): d.rounded_rectangle((P(k - 12), P(cy0 - 30), P(k + 12), P(cy0 + 34)), radius=P(10), fill=NAVY)
    mf = HEAD(64); mt = s.get("month", "DEC"); mb = mf.getbbox(mt); d.text((P((cx0 + cx1) / 2) - (mb[0] + mb[2]) / 2, P(cy0 + 62) - (mb[1] + mb[3]) / 2), mt, font=mf, fill=WHITE)
    dt = str(s.get("day", "1")); df = HEAD(300); db = df.getbbox(dt); d.text((P((cx0 + cx1) / 2) - (db[0] + db[2]) / 2, P(cy0 + 290) - (db[1] + db[3]) / 2), dt, font=df, fill=INK)
    if s.get("weekday"): wf = SEMI(30); d.text((P((cx0 + cx1) / 2) - wf.getlength(s["weekday"]) / 2, P(cy1 - 60)), s["weekday"], font=wf, fill=MUTED)
    pill(d, L, 110, s.get("eyebrow", "MARK YOUR CALENDAR"), NAVY, WHITE, 18)
    size = fit_head(s["head"], 500, 380, 110)
    y = draw_head(d, s["head"], L, 190, size, {"ink": NAVY, "blue": (196, 54, 54)}) + 16
    y = max(y, 640)
    y = text_block(d, s.get("sub", ""), BODY(34), L, y, 950, TEXT, 1.35, 2) + 30
    for i, t in enumerate(rows_of(s, 4)):
        g.card(im, (L, y, 850, y + 86), radius=20, fill=WHITE); d = ImageDraw.Draw(im)
        d.rectangle((P(L), P(y + 16), P(L + 8), P(y + 70)), fill=(196, 54, 54))
        ls = wrap(t, SEMI(31), P(720))[:2]; ty = y + 43 - len(ls) * 20
        for ln in ls: d.text((P(L + 36), P(ty)), ln, font=SEMI(31), fill=INK); ty += 40
        y += 104
    if s.get("bottom"): text_block(d, s["bottom"].upper(), HEAD(42), L, max(y + 10, 1110), 760, (196, 54, 54), 1.0, 1)
    logo(im, False, L, None, 250)
    howie(im, s.get("howie"), {"pose": "pointL", "x": 965, "feet": 1320, "h": 230})
    return finish(im, path)


NEW = {"checklist": l_checklist, "versus": l_versus, "stat": l_stat, "phone": l_phone, "steps": l_steps,
       "poll": l_poll, "bold": l_bold, "browser": l_browser, "question": l_question, "calendar": l_calendar}
L0.LAYOUTS.update(NEW)
