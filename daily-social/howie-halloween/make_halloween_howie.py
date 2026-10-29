"""Halloween reel v2: website horrors + Howie in a vampire costume. 1080x1920, 30fps."""
import sys, os, subprocess, json, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from video import Reel, WHITE, BLUE, GRAY, ORANGE, NAVY, W, H, FPS
from PIL import Image

OV = os.environ.get("OV", "/tmp/claude-0/howie/frames")
h = lambda t, c=WHITE, s=120, w=800: ("h", w, s, c, t)
b = lambda t, c=GRAY, s=46, w=600: ("b", w, s, c, t)
Y = 780  # text block centre, keeps clear of Howie (top of his head ~1210)
scenes = [dict(beats=6, y=Y, lines=[("emoji", "🎃", 160), ("gap", 10), h("Scariest website"), h("crimes we've seen", ORANGE, 110)])]
for e, a, c in [("💀", "A phone number", "you can't tap"), ("🕸️", "“© 2017”", "in the footer"), ("🧟", "A contact form", "that emails nobody"), ("🦇", "A 9-second", "load time"), ("👻", "No “Call” button", "anywhere")]:
    scenes.append(dict(beats=6, y=Y, lines=[("emoji", e, 150), ("gap", 10), h(a), h(c, ORANGE)]))
scenes.append(dict(beats=8, y=Y, lines=[h("Is your site"), h("haunted?", ORANGE, 170), ("gap", 10), b("Free quote · link in bio", WHITE, 50)]))

class HowieReel(Reel):
    def frame(self, t):
        im = super().frame(t).convert("RGBA")
        f = os.path.join(OV, "h%04d.png" % int(round(t * FPS)))
        if os.path.exists(f):
            im.alpha_composite(Image.open(f).convert("RGBA"), (0, 1000))
        return im.convert("RGB")

def sfx_mix(path, duration):
    """Add a whoosh on every Howie hop and a soft pop on each speech bubble."""
    T = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "howie", "timeline.json")))
    with wave.open(path) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32767
    rng = np.random.default_rng(3)
    prev = None
    for m in T["MV"]:
        if m.get("d"):
            n = int((m["d"] + .15) * sr); noise = rng.standard_normal(n)
            tt = np.arange(n) / sr; env = np.sin(np.pi * np.clip(tt / (m["d"] + .15), 0, 1)) ** 2
            # moving band-pass: cumulative one-pole with sweeping coefficient
            fc = 300 + 2500 * env; a = np.exp(-2 * np.pi * fc / sr); y = np.zeros(n); acc = 0.0
            for i in range(n): acc = a[i] * acc + (1 - a[i]) * noise[i]; y[i] = acc
            y = (noise - y) * 0.0 + y  # keep low-passed noise
            y = y / (np.abs(y).max() + 1e-9) * env * (0.32 if m["h"] > 150 else 0.2)
            pan = 1 if prev is None or m["x"] > prev else -1
            i0 = int(m["t"] * sr); j = min(len(x), i0 + n)
            x[i0:j, 0] += y[: j - i0] * (0.6 - 0.3 * pan); x[i0:j, 1] += y[: j - i0] * (0.6 + 0.3 * pan)
        prev = m["x"]
    for bu in T["BU"]:
        n = int(.12 * sr); tt = np.arange(n) / sr
        pop = np.sin(2 * np.pi * (900 - 2500 * tt) * tt) * np.exp(-tt * 45) * 0.35
        i0 = int(bu["t"] * sr); x[i0:i0 + n, :] += pop[:, None][: len(x) - i0]
    x = np.tanh(x * 1.05); x = x / np.abs(x).max() * 0.89
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    out = sys.argv[1]
    r = HowieReel(scenes, accent=ORANGE, music=4)
    if os.environ.get("MODE") == "stills":
        for k, t in enumerate([float(v) for v in sys.argv[2].split(",")]):
            r.frame(t).save(f"/tmp/claude-0/howie/still-{k}.png")
        sys.exit()
    tmp = out + ".silent.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(int(r.duration * FPS)): p.stdin.write(r.frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, "music.py"), f"{r.duration:.3f}", out + ".wav", "4"], check=True)
    sfx_mix(out + ".wav", r.duration)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", out + ".wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(tmp); os.remove(out + ".wav"); print(out, round(r.duration, 2))
