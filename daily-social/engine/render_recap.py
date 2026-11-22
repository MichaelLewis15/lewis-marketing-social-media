"""Monthly Client Results recap graphic for Lewis Marketing (Michael's request, Nov 22, 2026).

Goes out on the 1st of every month and celebrates the previous month across ALL client accounts combined.
Never names, shows or hints at a particular client (Michael's rule): totals and counts only.

usage: python3 render_recap.py spec.json [repo_root]
Writes <repo_root>/daily/x/<id>/s1.png (1080x1350).

spec = {
  "id": "2026-12-01-recap",
  "month": "NOVEMBER 2026",                          # the month being recapped
  "head": [["LAST MONTH WITH", "ink"], ["LEWIS MARKETING", "blue"]],   # optional
  "sub": "Combined results across the businesses we work with.",      # optional
  "stats": [                                         # 2-4, strongest first; real numbers only
    {"value": "899", "label": "new leads for our clients", "note": "up 28% from October"},
    {"value": "25", "label": "client businesses grew their leads"},
    {"value": "8", "label": "more than doubled them"}
  ],
  "footnote": "Combined HighLevel CRM data from client accounts Lewis Marketing manages, Nov 1-30, 2026. No individual client shown."
}
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
from graphics2 import P, W, H, INK, TEXT, MUTED, WHITE, HEAD, BODY, SEMI, wrap, card
from layouts import canvas, radial, dots, logo, howie, fit_head, draw_head, pill, finish, NAVY, SUN, SKY


def render(s, out):
    im = canvas(NAVY); radial(im, 240, 300, 560, SKY, 70); radial(im, 980, 1250, 460, SKY, 40); dots(im, (255, 255, 255), 18)
    d = ImageDraw.Draw(im); L = 70
    y = pill(d, L, 76, "CLIENT RESULTS  ·  " + s["month"].upper(), SUN, NAVY, 22) + 30
    head = s.get("head") or [["LAST MONTH WITH", "ink"], ["LEWIS MARKETING", "blue"]]
    size = fit_head(head, 940, 270, 128)
    y = draw_head(d, head, L, y, size, {"ink": WHITE, "blue": SUN, "dark": SKY}) + 10
    for ln in wrap(s.get("sub", "Combined results across the businesses we work with."), BODY(32), P(900))[:2]:
        d.text((P(L), P(y)), ln, font=BODY(32), fill=(214, 222, 234)); y += 46
    y += 26
    stats = s["stats"][:4]
    # first stat is the hero: full-width card; the rest share a row
    hero, rest = stats[0], stats[1:]
    hh = 250
    card(im, (L, y, W - L, y + hh), radius=30)
    d = ImageDraw.Draw(im)
    vf = HEAD(190); bb = vf.getbbox(hero["value"])
    d.text((P(L + 40) - bb[0], P(y + 30) - bb[1]), hero["value"], font=vf, fill=SKY)
    tx = L + 40 + (bb[2] - bb[0]) / P(1) + 34; tw = W - L - 40 - tx
    ty = y + 52
    for ln in wrap(hero["label"].upper(), HEAD(54), P(tw))[:2]: d.text((P(tx), P(ty)), ln, font=HEAD(54), fill=INK); ty += 56
    if hero.get("note"):
        for ln in wrap(hero["note"], SEMI(28), P(tw))[:2]: d.text((P(tx), P(ty + 8)), ln, font=SEMI(28), fill=(24, 120, 176)); ty += 38
    y += hh + 24
    if rest:
        n = len(rest); gap = 24; cw = (W - 2 * L - gap * (n - 1)) / n; ch = 250
        for i, st in enumerate(rest):
            x = L + i * (cw + gap)
            card(im, (x, y, x + cw, y + ch), radius=28); d = ImageDraw.Draw(im)
            vs = 150 if n < 3 else 120
            vf = HEAD(vs); bb = vf.getbbox(st["value"])
            d.text((P(x + 30) - bb[0], P(y + 26) - bb[1]), st["value"], font=vf, fill=SKY)
            ly = y + 30 + (bb[3] - bb[1]) / P(1) + 18
            for ln in wrap(st["label"], SEMI(28 if n < 3 else 25), P(cw - 60))[:3]:
                d.text((P(x + 30), P(ly)), ln, font=SEMI(28 if n < 3 else 25), fill=TEXT); ly += 38
        y += ch
    fy = H - 170
    for ln in wrap(s.get("footnote", ""), BODY(19), P(620))[:3]: d.text((P(L), P(fy)), ln, font=BODY(19), fill=(170, 184, 204)); fy += 27
    logo(im, True, L, H - 78, 250)
    # 3D Howie (Michael's rule, Nov 21, 2026): the WebGL render from howie3d/, not the flat SVG drawing.
    # Render once with: cd howie3d && python3 render.py '[{"out":"howie-cheer.png","pose":"cheer","mouth":"open"}]'
    hi = Image.open(os.path.join(HERE, "howie3d", "howie-cheer.png")).convert("RGBA"); hi = hi.crop(hi.getbbox())
    hh = P(330); hi = hi.resize((int(hi.width * hh / hi.height), hh), Image.LANCZOS)
    im.alpha_composite(hi, (P(925) - hi.width // 2, P(H - 30) - hi.height))
    return finish(im, out)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); root = sys.argv[2] if len(sys.argv) > 2 else os.path.abspath(os.path.join(HERE, "..", ".."))
    od = os.path.join(root, "daily", "x", spec["id"]); os.makedirs(od, exist_ok=True)
    print(render(spec, os.path.join(od, "s1.png")))
