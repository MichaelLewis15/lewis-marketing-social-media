"""Recognition / award graphic for Lewis Marketing (first used Nov 25, 2026: #5 on SEO App's 2026 Sioux City SEO list).

usage: python3 render_award.py spec.json [repo_root]
Writes <repo_root>/daily/x/<id>/s1.png (1080x1350 feed) and gbp.png (1200x900, Google Business Profile).

spec = {
  "id": "2026-11-26-seoapp-award",
  "eyebrow": "SEO APP · 2026 LIST",
  "rank": "#5",
  "title": ["TOP 10 SEO AGENCIES", "FOR SIOUX CITY, IA"],
  "sub": "Lewis Marketing made SEO App's 2026 list.",
  "facts": [["5.0", "Google rating"], ["27", "verified reviews"]],
  "footnote": "Source: SEO App, \"Sioux City, IA SEO: 10 Agencies That Made Our 2026 List\" (seoapp.io), ranked on verified Google ratings and review counts."
}
Only facts the source states. Never use the list publisher's logo.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
from graphics2 import P, W, H, INK, TEXT, WHITE, HEAD, BODY, SEMI, wrap, card
from layouts import canvas, radial, dots, logo, pill, finish, NAVY, SUN, SKY


def _howie(size):
    # 3D Howie (Michael's rule, Nov 21, 2026)
    hi = Image.open(os.path.join(HERE, "howie3d", "howie-cheer.png")).convert("RGBA"); hi = hi.crop(hi.getbbox())
    hh = P(size); return hi.resize((int(hi.width * hh / hi.height), hh), Image.LANCZOS)


def _badge(im, cx, cy, r, rank):
    d = ImageDraw.Draw(im)
    d.ellipse((P(cx - r - 14), P(cy - r - 14), P(cx + r + 14), P(cy + r + 14)), fill=SUN)
    d.ellipse((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), fill=NAVY, outline=WHITE, width=P(5))
    f = HEAD(int(r * 1.05)); d.text((P(cx), P(cy + 4)), rank, font=f, fill=SUN, anchor="mm")


def _facts(im, facts, x0, y, x1, h, vs=74, ls=24):
    n = len(facts); gap = 20; cw = (x1 - x0 - gap * (n - 1)) / n
    for i, (v, lab) in enumerate(facts):
        x = x0 + i * (cw + gap); card(im, (x, y, x + cw, y + h), radius=24); d = ImageDraw.Draw(im)
        d.text((P(x + cw / 2), P(y + h * 0.42)), v, font=HEAD(vs), fill=SKY, anchor="mm")
        d.text((P(x + cw / 2), P(y + h * 0.78)), lab, font=SEMI(ls), fill=TEXT, anchor="mm")


def render(s, out):
    im = canvas(NAVY); radial(im, 540, 470, 600, SKY, 80); radial(im, 960, 1250, 420, SKY, 40); dots(im, (255, 255, 255), 18)
    d = ImageDraw.Draw(im); L = 70
    pw = d.textlength(s["eyebrow"], font=SEMI(24)) / P(1) + 48
    pill(d, (W - pw) / 2, 70, s["eyebrow"], SUN, NAVY, 24)
    _badge(im, W / 2, 370, 190, s["rank"]); d = ImageDraw.Draw(im)
    y = 610
    for ln in s["title"]:
        f = HEAD(70); d.text((P(W / 2), P(y)), ln, font=f, fill=WHITE, anchor="ma"); y += 80
    y += 14
    for ln in wrap(s.get("sub", ""), BODY(34), P(900))[:2]:
        d.text((P(W / 2), P(y)), ln, font=BODY(34), fill=(214, 222, 234), anchor="ma"); y += 48
    y += 26
    if s.get("facts"): _facts(im, s["facts"], 170, y, 910, 160)
    d = ImageDraw.Draw(im); fy = H - 170
    for ln in wrap(s.get("footnote", ""), BODY(18), P(640))[:4]: d.text((P(L), P(fy)), ln, font=BODY(18), fill=(170, 184, 204)); fy += 25
    logo(im, True, L, H - 70, 230)
    hi = _howie(300); im.alpha_composite(hi, (P(940) - hi.width // 2, P(H - 20) - hi.height))
    return finish(im, out)


def render_gbp(s, out, GW=1200, GH=900):
    im = Image.new("RGBA", (P(GW), P(GH)), NAVY + (255,)); radial(im, 260, 330, 520, SKY, 80)
    d = ImageDraw.Draw(im)
    _badge(im, 250, 330, 165, s["rank"]); d = ImageDraw.Draw(im)
    x = 480; y = 120
    pill(d, x, y, s["eyebrow"], SUN, NAVY, 20); y += 80
    for ln in s["title"]:
        d.text((P(x), P(y)), ln, font=HEAD(54), fill=WHITE); y += 64
    y += 10
    for ln in wrap(s.get("sub", ""), BODY(28), P(GW - x - 60))[:2]: d.text((P(x), P(y)), ln, font=BODY(28), fill=(214, 222, 234)); y += 40
    if s.get("facts"): _facts(im, s["facts"], x, y + 26, GW - 60, 130, 60, 21)
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(wrap(s.get("footnote", ""), BODY(15), P(820))[:2]): d.text((P(60), P(GH - 70 + i * 20)), ln, font=BODY(15), fill=(170, 184, 204))
    lg = Image.open(os.path.join(HERE, "logo_white.png")).convert("RGBA"); lw = P(220)
    lg = lg.resize((lw, int(lw * lg.height / lg.width)), Image.LANCZOS); im.alpha_composite(lg, (P(60), P(GH - 180)))
    hi = _howie(250); im.alpha_composite(hi, (P(GW - 130) - hi.width // 2, P(GH - 20) - hi.height))
    im.convert("RGB").resize((GW, GH), Image.LANCZOS).save(out, optimize=True); return out


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); root = sys.argv[2] if len(sys.argv) > 2 else os.path.abspath(os.path.join(HERE, "..", ".."))
    od = os.path.join(root, "daily", "x", spec["id"]); os.makedirs(od, exist_ok=True)
    print(render(spec, os.path.join(od, "s1.png"))); print(render_gbp(spec, os.path.join(od, "gbp.png")))
