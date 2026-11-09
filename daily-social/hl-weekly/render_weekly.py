"""HighLevel Weekly: renders the Friday "What's new in HighLevel" recap for Lewis Marketing.

usage: python3 render_weekly.py spec.json OUTDIR
spec: {"week": "Nov 2-7, 2026", "items": [{"title": "...", "why": "...", "tag": "New"|"Beta"|"Update"}, ...3-5],
       "cta": "Want these set up in your account?", "music": 0-3}
outputs in OUTDIR:
  v916.mp4  1080x1920 (Instagram/Facebook reels, Threads, TikTok)
  v169.mp4  1920x1080 (YouTube, LinkedIn, Bluesky)
  gbp.png   1200x900 graphic (Google Business Profile, no video there)
  cover916.jpg / cover169.jpg posters
Howie (the real animated rig from howie/reel-generic.html) hops in, waves, points at each release and cheers at the end.
"""
import json, os, sys, subprocess, tempfile, math
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
O = lambda w, s: ImageFont.truetype(os.path.join(TOOLS, f"outfit-latin-{w}-normal.woff"), s)
S = lambda w, s: ImageFont.truetype(os.path.join(TOOLS, f"open-sans-latin-{w}-normal.woff"), s)
LOGO = Image.open(os.path.join(ENGINE, "logo_white.png")).convert("RGBA")
INTRO, ITEM, OUTRO = 3.2, 4.6, 4.2


def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def background(W, H):
    y, x = np.mgrid[0:H, 0:W]
    cx, cy = W * 0.72, H * 0.22
    r = np.sqrt(((x - cx) / W) ** 2 + ((y - cy) / H) ** 2)
    g = np.clip(1 - r * 1.6, 0, 1)[..., None]
    img = np.array(NAVY2, float) * (1 - g) + np.array(NAVY, float) * g
    im = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    step = 44 if W > H else 48
    for yy in range(step // 2, H, step):
        for xx in range(step // 2, W, step):
            d.ellipse((xx - 1.5, yy - 1.5, xx + 1.5, yy + 1.5), fill=(255, 255, 255, 18))
    glow = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(glow)
    gd.ellipse((W * 0.55, -H * 0.15, W * 1.1, H * 0.45), fill=(41, 162, 222, 70))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W // 8)))
    return im


def growth_line(d, W, H, p):
    pts = []
    for i in range(0, 41):
        t = i / 40
        if t > p: break
        x = t * W; y = H - 26 - (math.sin(t * 7) * 6 + t * 50)
        pts.append((x, y))
    if len(pts) > 1: d.line(pts, fill=SKY + (170,), width=5)


def pill(d, x, y, text, font, fill, fg):
    w = d.textlength(text, font=font); h = font.size + 22
    d.rounded_rectangle((x, y, x + w + 44, y + h), radius=h // 2, fill=fill)
    d.text((x + 22, y + h / 2), text, font=font, fill=fg, anchor="lm")
    return w + 44


def paste_logo(im, x, y, h, alpha=1.0, anchor="l"):
    lg = LOGO.resize((int(LOGO.width * h / LOGO.height), h), Image.LANCZOS)
    if alpha < 1: lg.putalpha(lg.getchannel("A").point(lambda v: int(v * alpha)))
    if anchor == "c": x -= lg.width // 2
    if anchor == "r": x -= lg.width
    im.alpha_composite(lg, (int(x), int(y)))


def layer_text(W, H, draw_fn, a=1.0, dy=0):
    L = Image.new("RGBA", (W, H)); draw_fn(ImageDraw.Draw(L))
    if a < 1: L.putalpha(L.getchannel("A").point(lambda v: int(v * a)))
    if dy: L = L.transform(L.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
    return L


class Layout:
    def __init__(self, W, H):
        self.W, self.H = W, H; self.v = H > W
        if self.v:  # 1080x1920; Howie lives bottom-left (x 80-330, y 1300-1600)
            self.x0, self.x1 = 90, W - 90; self.top = 330; self.foot = 1735
            self.f_head, self.f_title, self.f_why, self.f_num, self.f_small = O(800, 124), O(800, 88), S(400, 48), O(800, 230), S(600, 36)
        else:  # 1920x1080; Howie lives bottom-left (x 90-330, y 700-990)
            self.x0, self.x1 = 470, W - 110; self.top = 120; self.foot = 965
            self.f_head, self.f_title, self.f_why, self.f_num, self.f_small = O(800, 100), O(800, 72), S(400, 40), O(800, 180), S(600, 30)


def frame(L, bg, spec, t, total):
    W, H = L.W, L.H; im = bg.copy(); d = ImageDraw.Draw(im)
    growth_line(d, W, H, min(1, t / total * 1.05))
    n = len(spec["items"])
    # footer: full logo + site
    paste_logo(im, W / 2 if L.v else L.x0, L.foot - (10 if L.v else 30), 64 if L.v else 54, 0.95, "c" if L.v else "l")
    if L.v: d.text((W / 2, L.foot + 78), "lewismarketingoc.com", font=S(600, 30), fill=MIST, anchor="mm")
    else: d.text((W - 110, L.foot - 3), "lewismarketingoc.com", font=S(600, 28), fill=MIST, anchor="rm")
    if t < INTRO:
        k = t / 0.6
        def f(dd):
            pill(dd, L.x0, L.top + (180 if L.v else 70), "HIGHLEVEL THIS WEEK", S(600, 32 if L.v else 28), SKY + (255,), WHITE)
            y = L.top + (300 if L.v else 170)
            dd.text((L.x0, y), "What's new", font=L.f_head, fill=WHITE)
            dd.text((L.x0, y + L.f_head.size * 1.08), "in HighLevel", font=L.f_head, fill=YEL)
            dd.text((L.x0, y + L.f_head.size * 2.3), spec["week"], font=L.f_why, fill=MIST)
            dd.text((L.x0, y + L.f_head.size * 2.3 + L.f_why.size * 1.6), f"{n} updates worth knowing about", font=L.f_why, fill=WHITE)
        im.alpha_composite(layer_text(W, H, f, ease(k), int((1 - ease(k)) * 40)))
        return im
    t2 = t - INTRO
    if t2 < n * ITEM:
        i = int(t2 // ITEM); lt = t2 - i * ITEM; it = spec["items"][i]
        a = ease(lt / 0.45) * (1 - ease((lt - ITEM + 0.35) / 0.35))
        def f(dd):
            y = L.top + (120 if L.v else 30)
            dd.text((L.x0, y), f"{i + 1:02d}", font=L.f_num, fill=SKY + (255,))
            tag = (it.get("tag") or "New").upper()
            nx = L.x0 + dd.textlength(f"{i + 1:02d}", font=L.f_num) + 30
            pill(dd, nx, y + L.f_num.size * 0.38, tag, S(600, 30 if L.v else 26), (YEL if tag == "NEW" else SKY) + (255,), NAVY)
            dd.text((L.x1, y + L.f_num.size * 0.5), f"{i + 1} of {n}", font=L.f_small, fill=MIST, anchor="rm")
            y += L.f_num.size * 1.12
            for ln in wrap(dd, it["title"], L.f_title, L.x1 - L.x0)[:4]:
                dd.text((L.x0, y), ln, font=L.f_title, fill=WHITE); y += L.f_title.size * 1.12
            y += 26
            dd.rectangle((L.x0, y, L.x0 + 90, y + 7), fill=YEL)
            y += 40
            for ln in wrap(dd, it["why"], L.f_why, L.x1 - L.x0)[:5 if L.v else 3]:
                dd.text((L.x0, y), ln, font=L.f_why, fill=MIST); y += L.f_why.size * 1.45
        im.alpha_composite(layer_text(W, H, f, a, int((1 - ease(lt / 0.45)) * 50)))
        # progress dots
        for j in range(n):
            cx = (W / 2 - (n - 1) * 18 + j * 36) if L.v else (L.x0 + j * 30 + 8)
            cy = (L.top + 10) if L.v else (L.foot - 120)
            d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(YEL if j == i else (255, 255, 255, 60)))
        return im
    lt = t2 - n * ITEM; a = ease(lt / 0.5)
    def f(dd):
        y = L.top + (260 if L.v else 120)
        for ln in wrap(dd, spec.get("cta") or "Want these set up in your account?", L.f_head, L.x1 - L.x0):
            dd.text((L.x0, y), ln, font=L.f_head, fill=WHITE); y += L.f_head.size * 1.1
        y += 30
        dd.text((L.x0, y), "We'll handle the setup.", font=L.f_title, fill=YEL); y += L.f_title.size * 1.6
        pill(dd, L.x0, y, "Book a call: lewismarketingoc.com", S(600, 40 if L.v else 34), SKY + (255,), WHITE)
    im.alpha_composite(layer_text(W, H, f, a, int((1 - a) * 40)))
    return im


def render_base(spec, W, H, total, out):
    L = Layout(W, H); bg = background(W, H)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(int(round(total * FPS))):
        p.stdin.write(frame(L, bg, spec, f / FPS, total).convert("RGB").tobytes())
    p.stdin.close(); p.wait()


def howie_frames(total, tmp):
    T = howie_reel.timeline(total)
    # point at each release right after it appears
    n = (total - INTRO - OUTRO) / ITEM
    PO = [dict(t=0, p="idle"), dict(t=0.9, p="wave"), dict(t=2.6, p="idle")]
    MV = [dict(t=0, x=-200, y=1590, s=1.25), dict(t=0.2, x=200, y=1590, s=1.25, d=0.6, h=150)]
    for i in range(int(round(n))):
        t0 = INTRO + i * ITEM
        PO += [dict(t=t0 + 0.5, p="pointR", a=100), dict(t=t0 + 2.4, p="idle")]
        if i % 2 == 1: MV.append(dict(t=t0 + 2.8, x=225, y=1590, s=1.25, d=0.4, h=45))
        elif i: MV.append(dict(t=t0 + 2.8, x=200, y=1590, s=1.25, d=0.4, h=45))
    PO.append(dict(t=total - OUTRO + 0.4, p="cheer"))
    T = dict(MV=MV, PO=PO, BU=T["BU"])
    json.dump(T, open(f"{tmp}/tl.json", "w"))
    npm = subprocess.check_output(["npm", "root", "-g"]).decode().strip()
    subprocess.run(["node", os.path.join(TOOLS, "howie", "render_any.js"), os.path.join(TOOLS, "howie", "reel-generic.html"), f"{tmp}/tl.json", str(total), f"{tmp}/fr"],
                   check=True, env=dict(os.environ, NODE_PATH=npm))
    return T


def compose(base, tmp, oy, ox, scale, audio, out):
    ov = f"[1:v]scale=iw*{scale}:-1[h];[0:v][h]overlay={ox}:{oy}:eof_action=pass[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-framerate", str(FPS), "-i", f"{tmp}/fr/h%04d.png", "-i", audio,
                    "-filter_complex", ov, "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)


def gbp_graphic(spec, out):
    W, H = 1200, 900; im = background(W, H); d = ImageDraw.Draw(im)
    pill(d, 70, 60, "HIGHLEVEL THIS WEEK", S(600, 26), SKY + (255,), WHITE)
    d.text((70, 125), "What's new in HighLevel", font=O(800, 64), fill=WHITE)
    d.text((70, 205), spec["week"], font=S(400, 30), fill=YEL)
    y = 280
    for i, it in enumerate(spec["items"]):
        d.text((70, y), f"{i + 1:02d}", font=O(800, 44), fill=SKY)
        ln = wrap(d, it["title"], O(700, 34), 650)[:2]
        for k, l in enumerate(ln): d.text((150, y + 4 + k * 40), l, font=O(700, 34), fill=WHITE)
        y += 52 + 40 * (len(ln) - 1) + 22
    howie = Image.open(os.path.join(TOOLS, "howie", "howie-pointL.png")).convert("RGBA")
    howie = howie.resize((int(howie.width * 290 / howie.height), 290), Image.LANCZOS)
    im.alpha_composite(howie, (W - howie.width - 50, H - howie.height - 130))
    paste_logo(im, 70, H - 95, 54)
    d.text((W - 60, H - 68), "lewismarketingoc.com", font=S(600, 26), fill=MIST, anchor="rm")
    im.convert("RGB").save(out, quality=95)


def main(spec_path, outdir):
    spec = json.load(open(spec_path)); os.makedirs(outdir, exist_ok=True)
    n = len(spec["items"]); assert 3 <= n <= 5, "use 3 to 5 releases"
    total = INTRO + n * ITEM + OUTRO
    tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR", "/tmp"))
    music.render(total + 0.5, f"{tmp}/m.wav", spec.get("music", 1))
    T = howie_frames(total, tmp)
    howie_reel.sfx(f"{tmp}/m.wav", f"{tmp}/a.wav", T)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/a.wav", "-af", f"afade=t=out:st={total - 1.5}:d=1.5", f"{tmp}/af.wav"], check=True)
    render_base(spec, 1080, 1920, total, f"{tmp}/b916.mp4")
    compose(f"{tmp}/b916.mp4", tmp, 1000, 0, 1, f"{tmp}/af.wav", os.path.join(outdir, "v916.mp4"))
    render_base(spec, 1920, 1080, total, f"{tmp}/b169.mp4")
    compose(f"{tmp}/b169.mp4", tmp, 430, 20, 1, f"{tmp}/af.wav", os.path.join(outdir, "v169.mp4"))
    gbp_graphic(spec, os.path.join(outdir, "gbp.png"))
    for v in ("916", "169"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(INTRO - 0.6), "-i", os.path.join(outdir, f"v{v}.mp4"), "-frames:v", "1", "-q:v", "3",
                        os.path.join(outdir, f"cover{v}.jpg")], check=True)
    subprocess.run(["rm", "-rf", tmp])
    print(json.dumps({"seconds": total, "out": outdir}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
