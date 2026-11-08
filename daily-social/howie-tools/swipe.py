"""Turn a carousel (1080x1350 slides) into a 9:16 swipe-style reel with music and animated Howie.
usage: python3 swipe.py out.mp4 music_style slide1.png slide2.png ...
"""
import sys, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from video import W, H, F, B, NAVY, NAVY2, BLUE, WHITE, GRAY, HERE
import howie_reel

HOLD, XF = 2.9, 0.45
SC = 0.86; SW, SH = int(1080 * SC), int(1350 * SC); SX, SY = (W - SW) // 2, 120

def bg():
    im = Image.new("RGB", (W, H), NAVY2); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; c = tuple(int(NAVY2[i] + (NAVY[i] - NAVY2[i]) * (1 - abs(t - .4))) for i in range(3)); d.line([(0, y), (W, y)], fill=c)
    return im

def frame(slide, i, n):
    im = bg(); s = Image.open(slide).convert("RGB").resize((SW, SH), Image.LANCZOS)
    sh = Image.new("RGBA", (SW + 60, SH + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([30, 30, SW + 30, SH + 30], 28, fill=(0, 0, 0, 150))
    im.paste(sh.filter(ImageFilter.GaussianBlur(18)), (SX - 30, SY - 18), sh.filter(ImageFilter.GaussianBlur(18)))
    m = Image.new("L", (SW, SH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, SW, SH], 26, fill=255); im.paste(s, (SX, SY), m)
    d = ImageDraw.Draw(im); y = 1540; gap = 34; x0 = W - 82 - gap * (n - 1)
    for k in range(n):
        r = 11 if k == i else 7; d.ellipse([x0 + k * gap - r, y - r, x0 + k * gap + r, y + r], fill=BLUE if k == i else GRAY)
    f = F(700, 54); t = "Save this for later" if i == n - 1 else f"{i + 1} / {n}  ·  keep watching"
    d.text((W - 70, 1640), t, font=f, fill=WHITE, anchor="rm")
    d.text((W - 70, 1830), "lewismarketingoc.com", font=B(600, 34), fill=GRAY, anchor="rm")
    return im

def run(out, music, slides):
    tmp = tempfile.mkdtemp(dir="/tmp/claude-0"); n = len(slides); files = []
    for i, s in enumerate(slides):
        p = f"{tmp}/f{i}.png"; frame(s, i, n).save(p); files.append(p)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for k, p in enumerate(files): cmd += ["-loop", "1", "-t", f"{HOLD + (XF if k < n - 1 else 0) + (1.2 if k == n - 1 else 0):.2f}", "-i", p]
    fc = []; last = "[0:v]"; off = 0
    for k in range(1, n):
        off += HOLD; lab = f"[x{k}]"; fc.append(f"{last}[{k}:v]xfade=transition=slideleft:duration={XF}:offset={off:.2f}{lab}"); last = lab; off += 0  # offset accumulates hold only
    fc.append(f"{last}format=yuv420p,fps=30[v]")
    silent = f"{tmp}/s.mp4"
    subprocess.run(cmd + ["-filter_complex", ";".join(fc), "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", silent], check=True)
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", silent]))
    subprocess.run([sys.executable, os.path.join(HERE, "music.py"), f"{d:.3f}", f"{tmp}/m.wav", str(music)], check=True)
    withm = f"{tmp}/sm.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", f"{tmp}/m.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", withm], check=True)
    howie_reel.run(withm, out)
    subprocess.run(["rm", "-rf", tmp]); return d

if __name__ == "__main__":
    print(run(sys.argv[1], int(sys.argv[2]), sys.argv[3:]))
