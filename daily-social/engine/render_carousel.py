"""Carousel renderer for Lewis Marketing extras (Industry Playbook, Scam Alert).

usage: python3 render_carousel.py spec.json [repo_root]
Writes <repo_root>/daily/x/<id>/s1.png ... sN.png (1080x1350) and cover-gbp.png (1200x900, not normally used).

spec = {
  "id": "2026-11-17-playbook",
  "theme": "playbook" | "alert",
  "eyebrow": "INDUSTRY PLAYBOOK" | "SCAM ALERT",
  "tag": "MANUFACTURING",                          # playbook: the industry; alert: who it targets ("BUSINESS PAGES")
  "head": [["WHERE YOUR", "ink"], ["NEXT HIRE", "ink"], ["IS LOOKING", "blue"]],   # cover headline, 2-4 short lines
  "sub": "One sentence under the headline.",
  "slides": [{"title": "Short slide title", "body": "Two or three short sentences.", "tip": "optional one-line tip"}],   # 3-6
  "cta": {"head": "Want this done for you?", "sub": "One line.", "button": "lewismarketingoc.com"},
  "sources": ["FTC consumer alert, Nov 2026"]      # alert: required, printed on the last slide; playbook: any stat sources
}
Howie is on the cover and the last slide. Scam Alert Howie (Michael's rule, Nov 14, 2026): never smiling, concerned face, yellow hard hat and hi-vis safety vest (howie/howie-safety-*.png, made from howie/howie-safety.svg with shoot2.js). Logo on every slide (all white on blue, two-tone white on navy, color on light).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
import graphics2 as g
from graphics2 import P, W, H, BLUE, BLUE_D, INK, TEXT, MUTED, WHITE, RED, HEAD, BODY, SEMI, wrap
from layouts import canvas, radial, dots, logo, howie, fit_head, draw_head, pill, finish, NAVY, SUN, MIST, SKY

AMBER = (245, 158, 11); ALERT_BG = (24, 18, 18)


def hazard(im, y, h=26):
    d = ImageDraw.Draw(im); d.rectangle((0, P(y), P(W), P(y + h)), fill=SUN)
    for x in range(-60, W + 60, 52): d.polygon([(P(x), P(y + h)), (P(x + 26), P(y + h)), (P(x + 52), P(y)), (P(x + 26), P(y))], fill=INK)


def counter(d, i, n, col):
    t = "%d / %d" % (i, n); f = SEMI(22); d.text((P(W - 70) - f.getlength(t), P(64)), t, font=f, fill=col)


def cover(s, n, path):
    alert = s["theme"] == "alert"
    im = canvas(ALERT_BG if alert else NAVY)
    radial(im, 260, 420, 560, RED if alert else SKY, 60 if alert else 70); dots(im, (255, 255, 255), 18)
    if alert: hazard(im, 0); hazard(im, H - 26)
    d = ImageDraw.Draw(im); L = 70
    y = pill(d, L, 90, s.get("eyebrow", "INDUSTRY PLAYBOOK"), AMBER if alert else SUN, INK, 22) + 18
    if s.get("tag"): y = pill(d, L, y, s["tag"], (255, 255, 255, 40) if False else (58, 76, 110) if not alert else (80, 30, 30), WHITE, 18) + 34
    size = fit_head(s["head"], 900, 560, 176)
    y = draw_head(d, s["head"], L, y, size, {"ink": WHITE, "blue": AMBER if alert else SUN, "dark": SKY}) + 18
    for ln in wrap(s.get("sub", ""), BODY(36), P(820)): d.text((P(L), P(y)), ln, font=BODY(36), fill=(214, 222, 234)); y += 50
    d.text((P(L), P(H - 200)), "Swipe  >", font=SEMI(30), fill=AMBER if alert else SUN)
    counter(d, 1, n, (170, 184, 204))
    logo(im, True, L, None, 260)
    howie(im, s.get("howie"), {"pose": "safety-idle" if alert else "pointL", "x": 900, "feet": H - 60 - (26 if alert else 0), "h": 340 if alert else 330})
    return finish(im, path)


def slide(s, i, n, sl, path):
    alert = s["theme"] == "alert"
    im = canvas(MIST if not alert else (252, 248, 244)); d = ImageDraw.Draw(im); L = 80
    col = BLUE if not alert else RED
    d.rectangle((0, 0, P(16), P(H)), fill=col)
    d.text((P(L), P(80)), "%02d" % (i - 1), font=HEAD(150), fill=col)
    counter(d, i, n, MUTED)
    y = 290; tf = HEAD(84); lines = wrap(sl["title"].upper(), tf, P(900))
    while len(lines) > 3 and tf.size > P(56): tf = HEAD(tf.size // P(1) - 6); lines = wrap(sl["title"].upper(), tf, P(900))
    for ln in lines: d.text((P(L), P(y)), ln, font=tf, fill=INK); y += tf.size / P(1) * .95
    y += 40; bf = BODY(44)
    for para in str(sl.get("body", "")).split("\n"):
        for ln in wrap(para, bf, P(900)): d.text((P(L), P(y)), ln, font=bf, fill=TEXT); y += 64
        y += 20
    if sl.get("tip"):
        y = max(y + 30, 860); tip = sl["tip"]; tfnt = SEMI(36); tl = wrap(tip, tfnt, P(840)); hh = 44 + 52 * len(tl)
        d.rounded_rectangle((P(L), P(y), P(W - L), P(y + hh)), radius=P(22), fill=WHITE, outline=col, width=P(3))
        yy = y + 22
        for ln in tl: d.text((P(L + 30), P(yy)), ln, font=tfnt, fill=INK); yy += 52
    logo(im, False, L, None, 230)
    return finish(im, path)


def last(s, n, path):
    alert = s["theme"] == "alert"; c = s.get("cta") or {}
    im = canvas(BLUE if not alert else ALERT_BG)
    radial(im, 800, 300, 520, (255, 255, 255) if not alert else RED, 40); dots(im, (255, 255, 255), 20)
    if alert: hazard(im, 0)
    d = ImageDraw.Draw(im); L = 70
    head = [(t, "ink") for t in wrap(c.get("head", "Want help with this?").upper(), HEAD(130), P(900))][:3]
    size = fit_head(head, 900, 420, 140)
    y = draw_head(d, head, L, 150, size, {"ink": WHITE}) + 24
    for ln in wrap(c.get("sub", ""), BODY(36), P(880)): d.text((P(L), P(y)), ln, font=BODY(36), fill=WHITE); y += 52
    y += 40; f = SEMI(34); t = c.get("button", "lewismarketingoc.com"); tw = f.getlength(t)
    d.rounded_rectangle((P(L), P(y), P(L) + tw + P(70), P(y + 84)), radius=P(42), fill=WHITE if not alert else AMBER)
    d.text((P(L + 35), P(y + 20)), t, font=f, fill=BLUE_D if not alert else INK)
    if s.get("sources"):
        sy = H - 250; d.text((P(L), P(sy)), "SOURCES", font=SEMI(20), fill=(220, 232, 244)); sy += 34
        for src in s["sources"][:3]:
            for ln in wrap(src, BODY(22), P(560)): d.text((P(L), P(sy)), ln, font=BODY(22), fill=(230, 238, 246)); sy += 30
    counter(d, n, n, (220, 232, 244))
    logo(im, True, L, None, 260)
    howie(im, s.get("howie_end"), {"pose": "safety-pointL" if alert else "wave", "x": 900, "feet": H - 60, "h": 340 if alert else 330})
    return finish(im, path)


def main(spec_path, root):
    s = json.load(open(spec_path)); n = len(s["slides"]) + 2
    out = os.path.join(root, "daily", "x", s["id"]); os.makedirs(out, exist_ok=True)
    files = [cover(s, n, os.path.join(out, "s1.png"))]
    for i, sl in enumerate(s["slides"], start=2): files.append(slide(s, i, n, sl, os.path.join(out, "s%d.png" % i)))
    files.append(last(s, n, os.path.join(out, "s%d.png" % n)))
    print(json.dumps({"slides": [os.path.relpath(f, root) for f in files]}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.abspath(os.path.join(HERE, "..", "..")))
