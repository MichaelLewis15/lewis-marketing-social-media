"""Monthly Client Results recap graphics for Lewis Marketing (Michael's request, Nov 22, 2026).

Goes out on the 1st of every month and celebrates the previous month across ALL client accounts combined.
Never names, shows or hints at a particular client (Michael's rule): totals and counts only.

usage: python3 render_recap.py spec.json [repo_root]
Writes <repo_root>/daily/x/<id>/s1.png (1080x1350 feed: Facebook, Instagram, Threads, LinkedIn, Bluesky)
and gbp.png (1200x900, Google Business Profile).
The videos (YouTube 16:9, TikTok 9:16) come from the video engine's "results" format (daily-social/hl-weekly/engine.py).

spec = {
  "id": "2026-12-01-recap",
  "month": "NOVEMBER 2026",                          # the month being recapped
  "head": [["LAST MONTH WITH", "ink"], ["LEWIS MARKETING", "blue"]],   # optional
  "sub": "Combined results across the businesses we work with.",      # optional
  "stats": [                                         # 2-5 (hero + up to 4), strongest first; real numbers only
    {"value": "899", "label": "new leads for our clients", "note": "up 28% from October"},
    {"value": "25", "label": "client businesses grew their leads"},
    {"value": "8", "label": "client businesses more than doubled their leads"}
  ],
  "footnote": "Combined HighLevel CRM data from client accounts Lewis Marketing manages, Nov 1-30, 2026. No individual client shown."
}
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
from graphics2 import P, W, H, INK, TEXT, WHITE, HEAD, BODY, SEMI, wrap, card
from layouts import canvas, radial, dots, logo, fit_head, draw_head, pill, finish, NAVY, SUN, SKY


def _howie(size):
    # 3D Howie (Michael's rule, Nov 21, 2026): the WebGL render from howie3d/, not the flat SVG drawing.
    # Re-render with: cd howie3d && python3 render.py '[{"out":"howie-cheer.png","pose":"cheer","mouth":"open"}]'
    hi = Image.open(os.path.join(HERE, "howie3d", "howie-cheer.png")).convert("RGBA"); hi = hi.crop(hi.getbbox())
    hh = P(size); return hi.resize((int(hi.width * hh / hi.height), hh), Image.LANCZOS)


def _hero(im, st, x0, y0, x1, h, vsize=180):
    card(im, (x0, y0, x1, y0 + h), radius=30); d = ImageDraw.Draw(im)
    vf = HEAD(vsize); bb = vf.getbbox(st["value"])
    vy = y0 + (h - (bb[3] - bb[1]) / P(1)) / 2
    d.text((P(x0 + 36) - bb[0], P(vy) - bb[1]), st["value"], font=vf, fill=SKY)
    tx = x0 + 36 + (bb[2] - bb[0]) / P(1) + 30; tw = x1 - 36 - tx
    lines = wrap(st["label"].upper(), HEAD(50 if h > 160 else 40), P(tw))[:2]
    notes = wrap(st["note"], SEMI(26), P(tw))[:2] if st.get("note") else []
    hf = 50 if h > 160 else 40
    ty = y0 + (h - (len(lines) * (hf + 2) + len(notes) * 36 + (8 if notes else 0))) / 2
    for ln in lines: d.text((P(tx), P(ty)), ln, font=HEAD(hf), fill=INK); ty += hf + 2
    ty += 8
    for ln in notes: d.text((P(tx), P(ty)), ln, font=SEMI(26), fill=(24, 120, 176)); ty += 36


def _small(im, st, x, y, cw, ch, vsize, lsize):
    card(im, (x, y, x + cw, y + ch), radius=26); d = ImageDraw.Draw(im)
    vf = HEAD(vsize); bb = vf.getbbox(st["value"])
    d.text((P(x + 28) - bb[0], P(y + 22) - bb[1]), st["value"], font=vf, fill=SKY)
    ly = y + 22 + (bb[3] - bb[1]) / P(1) + 14
    for ln in wrap(st["label"], SEMI(lsize), P(cw - 56))[:3]:
        d.text((P(x + 28), P(ly)), ln, font=SEMI(lsize), fill=TEXT); ly += lsize * 1.35


def _grid(im, rest, x0, y0, x1, ch, gap=20, cols=None, vs=None, ls=None):
    n = len(rest); cols = cols or (2 if n == 4 else n); rows = (n + cols - 1) // cols
    cw = (x1 - x0 - gap * (cols - 1)) / cols
    dv, dl = (88, 24) if rows > 1 or cols > 2 else (140, 27); vs = vs or dv; ls = ls or dl
    for i, st in enumerate(rest):
        r, c = divmod(i, cols); _small(im, st, x0 + c * (cw + gap), y0 + r * (ch + gap), cw, ch, vs, ls)
    return y0 + rows * ch + (rows - 1) * gap


def render(s, out):
    """Feed graphic, 1080x1350."""
    im = canvas(NAVY); radial(im, 240, 300, 560, SKY, 70); radial(im, 980, 1250, 460, SKY, 40); dots(im, (255, 255, 255), 18)
    d = ImageDraw.Draw(im); L = 70
    y = pill(d, L, 70, "CLIENT RESULTS  ·  " + s["month"].upper(), SUN, NAVY, 22) + 26
    head = s.get("head") or [["LAST MONTH WITH", "ink"], ["LEWIS MARKETING", "blue"]]
    size = fit_head(head, 940, 240, 118)
    y = draw_head(d, head, L, y, size, {"ink": WHITE, "blue": SUN, "dark": SKY}) + 8
    for ln in wrap(s.get("sub", "Combined results across the businesses we work with."), BODY(30), P(920))[:2]:
        d.text((P(L), P(y)), ln, font=BODY(30), fill=(214, 222, 234)); y += 42
    y += 22
    stats = s["stats"][:5]; hero, rest = stats[0], stats[1:]
    two_rows = len(rest) == 4
    hh = 200 if two_rows else 240
    _hero(im, hero, L, y, W - L, hh, 160 if two_rows else 185); y += hh + 20
    if rest: _grid(im, rest, L, y, W - L, 196 if two_rows else 240)
    d = ImageDraw.Draw(im); fy = H - 168
    for ln in wrap(s.get("footnote", ""), BODY(18), P(640))[:3]: d.text((P(L), P(fy)), ln, font=BODY(18), fill=(170, 184, 204)); fy += 25
    logo(im, True, L, H - 76, 240)
    hi = _howie(240 if two_rows else 320)
    im.alpha_composite(hi, (P(930) - hi.width // 2, P(H - 22) - hi.height))
    return finish(im, out)


def render_gbp(s, out, GW=1200, GH=900):
    """Google Business Profile graphic, 1200x900 (4:3), same content."""
    im = Image.new("RGBA", (P(GW), P(GH)), NAVY + (255,)); radial(im, 220, 220, 520, SKY, 70); radial(im, 1100, 860, 420, SKY, 40)
    d = ImageDraw.Draw(im); L = 60
    y = pill(d, L, 52, "CLIENT RESULTS  ·  " + s["month"].upper(), SUN, NAVY, 20) + 22
    head = s.get("head") or [["LAST MONTH WITH", "ink"], ["LEWIS MARKETING", "blue"]]
    size = fit_head(head, 700, 150, 84)
    y = draw_head(d, head, L, y, size, {"ink": WHITE, "blue": SUN, "dark": SKY}) + 22
    stats = s["stats"][:5]; hero, rest = stats[0], stats[1:]
    _hero(im, hero, L, y, GW - 300, 150, 120); y += 150 + 16
    if rest:
        cols = 2 if len(rest) > 2 else len(rest)
        _grid(im, rest, L, y, GW - 300, 168 if len(rest) > 2 else 200, 16, cols=cols, vs=72 if len(rest) > 2 else 110, ls=21 if len(rest) > 2 else 24)
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(wrap(s.get("footnote", ""), BODY(15), P(860))[:2]):
        d.text((P(L), P(GH - 62 + i * 20)), ln, font=BODY(15), fill=(170, 184, 204))
    lg = Image.open(os.path.join(HERE, "logo_white.png")).convert("RGBA"); lw = P(210)
    lg = lg.resize((lw, int(lw * lg.height / lg.width)), Image.LANCZOS)
    im.alpha_composite(lg, (P(GW - 60) - lg.width, P(48)))
    hi = _howie(250); im.alpha_composite(hi, (P(GW - 150) - hi.width // 2, P(GH - 76) - hi.height))
    im.convert("RGB").resize((GW, GH), Image.LANCZOS).save(out, optimize=True); return out


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); root = sys.argv[2] if len(sys.argv) > 2 else os.path.abspath(os.path.join(HERE, "..", ".."))
    od = os.path.join(root, "daily", "x", spec["id"]); os.makedirs(od, exist_ok=True)
    print(render(spec, os.path.join(od, "s1.png"))); print(render_gbp(spec, os.path.join(od, "gbp.png")))
