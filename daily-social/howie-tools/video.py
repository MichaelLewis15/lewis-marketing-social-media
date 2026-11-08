"""Kinetic-type branded reels for Lewis Marketing. 1080x1920 @30fps, cuts on the beat."""
import math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H, FPS = 1080, 1920, 30
BPM = 126; BEAT = 60 / BPM
HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda w, s: ImageFont.truetype(os.path.join(HERE, f"outfit-latin-{w}-normal.woff"), s)
B = lambda w, s: ImageFont.truetype(os.path.join(HERE, f"open-sans-latin-{w}-normal.woff"), s)
EMOJI = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)

NAVY = (11, 31, 51); NAVY2 = (6, 18, 32); BLUE = (41, 162, 222); WHITE = (255, 255, 255)
GRAY = (176, 196, 214); ORANGE = (255, 138, 36)

def hexrgb(c): return c

def ease_out_back(x):
    x = max(0, min(1, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def ease_out(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def emoji_img(ch, size):
    im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=EMOJI, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)

def text_img(txt, font, color, maxw=940):
    # shrink to fit
    f = font
    while f.getlength(txt) > maxw and f.size > 30:
        f = ImageFont.truetype(f.path, f.size - 4)
    bb = f.getbbox(txt)
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] + 30), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 10), txt, font=f, fill=color)
    return im

def make_bg(accent):
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    base = np.array(NAVY)[None, None, :] * (1 - y[..., None] * 0.5) + np.array(NAVY2)[None, None, :] * (y[..., None] * 0.5)
    base = np.broadcast_to(base, (H, W, 3)).copy()
    return Image.fromarray(base.astype(np.uint8))

class Reel:
    def __init__(self, scenes, accent=BLUE, footer="lewismarketingoc.com", music=0):
        self.music = music
        self.scenes = scenes; self.accent = accent; self.footer = footer
        self.bg = make_bg(accent)
        # glow blob
        g = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((150, 150, 750, 750), fill=accent + (120,))
        self.glow = g.filter(ImageFilter.GaussianBlur(140))
        lg = Image.open(os.path.join(HERE, "logo_white.png")).convert("RGBA")
        self.word = lg.resize((400, round(400 * lg.height / lg.width)), Image.LANCZOS)
        self.url = text_img(footer, B(600, 30), GRAY)
        # prerender scene elements
        self.t0s = []; t = 0
        for s in scenes:
            self.t0s.append(t); t += s["beats"] * BEAT
            s["_items"] = []
            for it in s["lines"]:
                kind = it[0]
                if kind == "emoji":
                    s["_items"].append(("img", emoji_img(it[1], it[2])))
                elif kind == "emojirow":
                    ims = [emoji_img(e, it[2]) for e in it[1]]
                    gap = int(it[2] * .35)
                    row = Image.new("RGBA", (sum(i.width for i in ims) + gap * (len(ims) - 1), max(i.height for i in ims)), (0, 0, 0, 0))
                    x = 0
                    for e in ims: row.alpha_composite(e, (x, (row.height - e.height) // 2)); x += e.width + gap
                    s["_items"].append(("img", row))
                elif kind == "pill":
                    ti = text_img(it[1], F(700, it[2]), NAVY if it[3] == WHITE else WHITE)
                    pad = 26
                    p = Image.new("RGBA", (ti.width + pad * 2, ti.height + 10), (0, 0, 0, 0))
                    ImageDraw.Draw(p).rounded_rectangle((0, 0, p.width - 1, p.height - 1), radius=p.height // 2, fill=it[3])
                    p.alpha_composite(ti, (pad, 2))
                    s["_items"].append(("img", p))
                elif kind == "gap":
                    s["_items"].append(("gap", it[1]))
                else:
                    weight, size, color = it[1], it[2], it[3]
                    font = F(weight, size) if kind == "h" else B(weight, size)
                    s["_items"].append(("img", text_img(it[4], font, color)))
        self.duration = t

    def frame(self, t):
        im = self.bg.copy().convert("RGBA")
        # drifting glow, pulses on beat
        beat_phase = (t % BEAT) / BEAT
        pulse = math.exp(-beat_phase * 5)
        gx = int(540 - 450 + 260 * math.sin(t * 0.7)); gy = int(700 - 450 + 300 * math.cos(t * 0.5))
        im.alpha_composite(self.glow, (gx, gy))
        d = ImageDraw.Draw(im)
        # diagonal accent stripes moving
        off = (t * 120) % 160
        ov = Image.new("RGBA", (W, 320), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(-2, 9):
            x = int(k * 160 + off) - 200
            od.polygon([(x, 320), (x + 40, 320), (x + 360, 0), (x + 320, 0)], fill=self.accent + (40,))
        im.alpha_composite(ov, (0, H - 320))
        # find scene
        i = max(j for j, s0 in enumerate(self.t0s) if s0 <= t)
        s = self.scenes[i]; lt = t - self.t0s[i]; sd = s["beats"] * BEAT
        # beat-pulsing accent bar on left
        bar_h = int(220 + 80 * pulse)
        d.rectangle((0, 860 - bar_h // 2, 16, 860 + bar_h // 2), fill=self.accent)
        # items: stack vertically centered
        items = s["_items"]
        heights = [it[1] if it[0] == "gap" else it[1].height for it in items]
        total = sum(heights) + 14 * (len(items) - 1)
        y = s.get("y", 900) - total // 2
        out_t = max(0, (lt - (sd - 0.18)) / 0.18)  # exit
        for k, it in enumerate(items):
            if it[0] == "gap":
                y += it[1] + 14; continue
            img = it[1]
            delay = 0.07 * k
            p = ease_out_back((lt - delay) / 0.38)
            a = ease_out((lt - delay) / 0.25) * (1 - out_t)
            if a <= 0:
                y += img.height + 14; continue
            dy = int((1 - p) * 90) - int(out_t * 60)
            x = (W - img.width) // 2 if s.get("align", "c") == "c" else 90
            layer = img
            if a < 1:
                layer = img.copy(); al = layer.getchannel("A").point(lambda v: int(v * a)); layer.putalpha(al)
            im.alpha_composite(layer, (x, y + dy))
            y += img.height + 14
        if s.get("draw"):
            s["draw"](im, lt, sd, out_t)
            d = ImageDraw.Draw(im)
        # scene-cut flash wipe
        if lt < 0.12 and i > 0:
            w = int(W * (1 - lt / 0.12))
            d.rectangle((W - w, 0, W, H), fill=self.accent + (255,))
        # top progress bar
        d.rectangle((0, 0, int(W * t / self.duration), 12), fill=self.accent)
        # footer
        im.alpha_composite(self.word, ((W - self.word.width) // 2, H - 290))
        im.alpha_composite(self.url, ((W - self.url.width) // 2, H - 150))
        return im.convert("RGB")

    def render(self, out, audio):
        tmp = out + ".silent.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        n = int(self.duration * FPS)
        for f in range(n):
            p.stdin.write(self.frame(f / FPS).tobytes())
        p.stdin.close(); p.wait()
        subprocess.run([sys.executable, os.path.join(HERE, "music.py"), f"{self.duration:.3f}", out + ".wav", str(self.music)], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", out + ".wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", out], check=True)
        os.remove(tmp); os.remove(out + ".wav")
