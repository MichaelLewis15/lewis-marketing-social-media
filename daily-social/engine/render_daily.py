"""daily-social graphic renderer for Lewis Marketing.

Usage:  python3 render_daily.py spec.json [repo_root]
Writes  <repo_root>/daily/<date>.png      (1080x1350, 4:5 feed graphic)
        <repo_root>/daily/gbp/<date>.png  (1200x900, 4:3 Google Business Profile version)

spec.json:
{
  "date": "2026-10-31",
  "eyebrow": "FRIDAY FIX",                       # small caps line at the top (no emojis)
  "head": [["YOUR GOOGLE", "ink"], ["PROFILE IS", "ink"], ["HALF DONE", "blue"]],   # 2-4 short lines
  "sub": "One sentence that names the problem.",
  "rows": [["1", "Step one"], ["2", "Step two"], ["3", "Step three"]],   # 3-5 rows, under ~32 chars each
  "bottom": "One-sentence takeaway.",
  "visual": {"kind": "checklist", "title": "GOOGLE PROFILE", "items": ["Hours", "Photos", "Services"]},
  "note": "Takes 10\nminutes",                    # optional handwritten note, max 2 short lines
  "wave": "LINE ONE\nLINE TWO"                   # optional footer tagline
}
"howie": {"pose": "pointL", "x": 985, "feet": 1110, "h": 215}   # optional: Howie, the Lewis Marketing robot
                                                 # poses: idle | pointL | pointR | wave | cheer. Use him on some posts, not all.
visual.kind: checklist | steps | profile | chat | bars | scan | phone
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graphics2 as g
from graphics2 import P, BLUE, BLUE_D, BLUE_L, INK, TEXT, MUTED, LINE, WHITE, RED, GREEN, HEAD, BODY, SEMI, OUTF, shadow, icon, card, spaced, spaced_len, wrap
from PIL import Image, ImageDraw, ImageFilter

COL = {"ink": INK, "blue": BLUE, "dark": BLUE_D}


def v_checklist(title, items, done=None, pill=None, cross=False):
    done = done if done is not None else max(1, len(items) - 2)
    def draw(im):
        card(im, (670, 200, 1040, 860), radius=26)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((P(670), P(200), P(1040), P(290)), radius=P(26), fill=BLUE)
        d.rectangle((P(670), P(262), P(1040), P(290)), fill=BLUE)
        f = SEMI(22); t = title.upper()[:22]; tw = spaced_len(t, f, .2)
        spaced(d, (P(855) - tw / 2, P(232)), t, f, WHITE, .2)
        n = len(items[:6]); y = 320; step = min(92, 500 / max(n, 1))
        for i, it in enumerate(items[:6]):
            ok = i < done
            d.rounded_rectangle((P(700), P(y), P(744), P(y + 44)), radius=P(10), fill=BLUE_L if ok else (244, 247, 250), outline=None if ok else LINE, width=P(2))
            if ok: icon(d, "check", 722, y + 22, 16, BLUE)
            elif cross: icon(d, "x", 722, y + 22, 14, RED)
            ff = SEMI(24) if len(it) <= 18 else SEMI(20)
            d.text((P(764), P(y + 6)), it[:24], font=ff, fill=INK if ok else MUTED)
            if cross and not ok:
                tl = ff.getlength(it[:24]); d.line([(P(764), P(y + 22)), (P(764) + tl, P(y + 22))], fill=RED, width=P(2))
            y += step
        shadow(im, lambda dd, c: dd.rounded_rectangle((P(610), P(800), P(930), P(880)), radius=P(40), fill=c), blur=18, alpha=60)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((P(610), P(800), P(930), P(880)), radius=P(40), fill=INK)
        icon(d, "check", 656, 840, 20, GREEN)
        t = (pill or "%d of %d done" % (done, n))[:20]; d.text((P(690), P(818)), t, font=SEMI(28), fill=WHITE)
    return draw


def v_steps(label):
    def draw(im):
        d = ImageDraw.Draw(im); base_y = 880
        for i in range(3):
            x0 = 690 + i * 118; h_ = 170 + i * 150
            shadow(im, lambda dd, c, x0=x0, h_=h_: dd.rounded_rectangle((P(x0), P(base_y - h_), P(x0 + 104), P(base_y)), radius=P(12), fill=c), blur=14, alpha=55)
            gr = g.vgrad(P(104), P(h_), (96, 194, 240), BLUE_D)
            m = Image.new("L", gr.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, gr.width - 1, gr.height - 1), radius=P(12), fill=255)
            im.paste(gr, (P(x0), P(base_y - h_)), m)
            d = ImageDraw.Draw(im); f = HEAD(96); t = str(i + 1); tw = f.getlength(t)
            d.text((P(x0 + 52) - tw / 2, P(base_y - h_ + 12)), t, font=f, fill=WHITE)
        icon(d, "person", 1002, base_y - 470 - 70, 46, INK)
        d.rounded_rectangle((P(680), P(base_y), P(1050), P(base_y + 10)), radius=P(5), fill=(205, 214, 222))
        lab = label.upper()[:30]; f2 = SEMI(17); tw = spaced_len(lab, f2, .25)
        spaced(d, (P(865) - tw / 2, P(base_y + 30)), lab, f2, MUTED, .25)
    return draw


def v_scan(url="yourwebsite.com", title="YOUR SCORECARD", rows=None):
    rows = rows or [("chart", "What's working", BLUE), ("x", "What's leaking", RED), ("star", "What to fix first", GREEN)]
    def draw(im):
        card(im, (660, 190, 1040, 800), radius=26)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((P(660), P(190), P(1040), P(246)), radius=P(26), fill=(30, 36, 44))
        d.rectangle((P(660), P(220), P(1040), P(246)), fill=(30, 36, 44))
        for i, c in enumerate([(239, 83, 80), (255, 193, 7), (76, 175, 80)]):
            d.ellipse((P(684 + i * 26), P(210), P(700 + i * 26), P(226)), fill=c)
        d.rounded_rectangle((P(770), P(206), P(1020), P(230)), radius=P(12), fill=(58, 66, 78))
        d.text((P(784), P(209)), url[:24], font=BODY(15), fill=(200, 208, 218))
        d.text((P(690), P(272)), title.upper()[:24], font=SEMI(17), fill=MUTED)
        cx, cy, r = 850, 440, 120
        d.arc((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), 180, 360, fill=BLUE_L, width=P(26))
        d.arc((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), 180, 268, fill=RED, width=P(26))
        f = HEAD(64); t = "?"; tw = f.getlength(t); d.text((P(cx) - tw / 2, P(cy - 74)), t, font=f, fill=INK)
        y = 520
        for k, txt, col in [(a, b, c if isinstance(c, tuple) else BLUE) for a, b, c in rows][:3]:
            d.rounded_rectangle((P(690), P(y), P(1010), P(y + 62)), radius=P(14), fill=(244, 247, 250))
            icon(d, k, 722, y + 31, 15, col)
            d.text((P(752), P(y + 18)), txt[:22], font=SEMI(21), fill=INK); y += 76
    return draw


def visual_for(v):
    k = (v or {}).get("kind", "checklist")
    if k == "checklist": return v_checklist(v.get("title", "CHECKLIST"), v.get("items", ["Step one", "Step two", "Step three"]), v.get("done"), v.get("pill"), v.get("cross", False))
    if k == "steps": return v_steps(v.get("label", "ONE STEP AT A TIME"))
    if k == "scan": return v_scan(v.get("url", "yourwebsite.com"), v.get("title", "YOUR SCORECARD"))
    return {"profile": g.v_profile, "chat": g.v_chat, "bars": g.v_bars, "phone": g.v_phone}.get(k, v_checklist("CHECKLIST", ["Step one", "Step two", "Step three"]))


def main(spec_path, root):
    s = json.load(open(spec_path))
    date = s["date"]
    out = os.path.join(root, "daily"); os.makedirs(os.path.join(out, "gbp"), exist_ok=True)
    g.OUT = out
    cfg = dict(eyebrow=s.get("eyebrow", "DAILY TIP"), head=[(t, COL.get(c, INK)) for t, c in s["head"]],
               sub=s["sub"], rows=[tuple(r) for r in s["rows"]], bottom=s["bottom"], visual=visual_for(s.get("visual")),
               note=s.get("note"), wave=s.get("wave", "STRATEGY FIRST.\nRESULTS THAT MATTER."), colw=s.get("colw", 560), howie=s.get("howie"))
    p = g.render(date, cfg)
    src = Image.open(p).convert("RGB")
    bg = src.resize((1200, 1500)).crop((0, 300, 1200, 1200)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (12, 26, 44)), .35)
    fg = src.resize((720, 900), Image.LANCZOS); bg.paste(fg, (240, 0))
    gp = os.path.join(out, "gbp", date + ".png"); bg.save(gp, optimize=True)
    print(json.dumps({"file": "daily/%s.png" % date, "gbp": "daily/gbp/%s.png" % date}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.abspath(os.path.join(HERE, "..", "..")))
