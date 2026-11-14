"""YouTube thumbnail maker: two versions (A and B) for YouTube Studio's "Test & compare".

usage:
  python3 thumb.py SPEC.json OUTDIR          uses spec["thumbnail"], the footage in spec["source"] and its "keep" parts
  (clip.py render runs it too when the spec has "thumbnail")

spec["thumbnail"] = {
  "a": {"text": "Hook for version A", "highlight": "word or phrase", "eyebrow": "THE MARKETING LENS"},
  "b": {"text": "A different angle", "highlight": "...", "eyebrow": "..."},
  "frames": [12.4, 31.0]   optional source times to use; otherwise the best face frames are picked
}
Rules: 3 to 6 words of hook text (it must read on a phone at the size of a stamp), different wording AND a different
look for A and B so the test teaches something, no emojis, no clickbait the video does not pay off.
Outputs thumb-a.jpg and thumb-b.jpg (1280x720, under 2 MB) plus thumb-frames.json (which frames were used).
Look: A navy panel with a sky accent; B full brand blue with the all-white logo. The face is cut out when rembg is
installed (it is in the cloud render); otherwise the frame fades into the panel.
"""
import json, os, re, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import clip
from clip import O, S, NAVY, NAVY2, SKY, BLUE, YEL, WHITE, logo, wrap
W, H = 1280, 720


def cascade(name):
    import cv2
    c = cv2.CascadeClassifier(os.path.join(HERE, name)); return c


def best_frames(src, keep, n=2, gap=3.0):
    """score frames on face size, sharpness and open eyes; return the n best source times, at least `gap` apart"""
    import cv2
    face, eye = cascade("haarcascade_frontalface_default.xml"), cascade("haarcascade_eye.xml")
    cands = []
    for a, b in keep:
        for t in np.arange(a + 0.5, b - 0.3, 0.5):
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=640:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
            if not r.stdout: continue
            img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_GRAYSCALE)
            fs = face.detectMultiScale(img, 1.1, 5, minSize=(60, 60))
            if not len(fs): continue
            x, y, w, h = max(fs, key=lambda f: f[2] * f[3]); roi = img[y:y + h, x:x + w]
            sharp = cv2.Laplacian(roi, cv2.CV_64F).var()
            eyes = len(eye.detectMultiScale(roi[: h // 2], 1.1, 6, minSize=(w // 10, w // 10)))
            cands.append((w * h / 1000 * min(sharp, 400) / 100 * (1.4 if eyes >= 2 else 1.0), float(t)))
    cands.sort(reverse=True); out = []
    for sc, t in cands:
        if all(abs(t - u) >= gap for u in out): out.append(t)
        if len(out) == n: break
    return out or [keep[0][0] + 1.0]


def grab(src, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True)
    import io; return Image.open(io.BytesIO(r.stdout)).convert("RGB")


def face_box(im):
    import cv2
    g = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY); fs = cascade("haarcascade_frontalface_default.xml").detectMultiScale(g, 1.1, 5, minSize=(80, 80))
    if not len(fs): return (im.width // 2 - im.height // 6, im.height // 4, im.height // 3, im.height // 3)
    return tuple(int(v) for v in max(fs, key=lambda f: f[2] * f[3]))


def person(im, box, size_h):
    """crop head and shoulders around the face, scaled to size_h; cut out with rembg when it is installed"""
    x, y, w, h = box; cx = x + w / 2
    top = max(0, y - h * 0.55); bot = min(im.height, y + h * 2.6); ht = bot - top; wd = ht * 0.85
    l = max(0, min(im.width - wd, cx - wd / 2)); crop = im.crop((int(l), int(top), int(l + wd), int(bot)))
    crop = crop.resize((int(crop.width * size_h / crop.height), size_h), Image.LANCZOS)
    try:
        from rembg import remove
        cut = remove(crop); return cut, True
    except Exception:
        m = Image.new("L", crop.size, 0); md = ImageDraw.Draw(m)
        md.rectangle((int(crop.width * 0.22), 0, crop.width, crop.height), fill=255)
        return Image.merge("RGBA", (*crop.split(), m.filter(ImageFilter.GaussianBlur(crop.width * 0.12)))), False


def pump(im, k=1.12):
    from PIL import ImageEnhance
    return ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(k)).enhance(1.06)


def make(frame, v, look, out):
    bg1, bg2, lg = ((NAVY, NAVY2, "white") if look == "a" else (BLUE, (3, 84, 168), "allwhite"))
    y = np.linspace(0, 1, H)[:, None, None]; x = np.linspace(0, 1, W)[None, :, None]
    arr = np.array(bg1, float) * (1 - 0.6 * x) + np.array(bg2, float) * (0.6 * x) * (0.7 + 0.3 * y)
    im = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
    if look == "a" and cut_ok():
        d.ellipse((760, 40, 1400, 680), fill=SKY + (255,))
    else:
        d.polygon([(820, 0), (W, 0), (W, H), (700, H)], fill=YEL + (255,))
    fr = pump(frame); box = face_box(fr); pc, cut = person(fr, box, 760 if cut_ok() else H)
    if cut: im.alpha_composite(pc, (W - pc.width + 40, H - pc.height + 40))
    else: im.alpha_composite(pc, (W - pc.width, 0))
    # text panel
    x0 = 60; yy = 60
    if v.get("eyebrow"):
        f = S(600, 28); tw = d.textlength(v["eyebrow"], font=f)
        d.rounded_rectangle((x0, yy, x0 + tw + 40, yy + 50), radius=25, fill=(SKY if look == "a" else NAVY) + (255,))
        d.text((x0 + 20, yy + 25), v["eyebrow"], font=f, fill=WHITE, anchor="lm"); yy += 78
    text = v["text"]; hl = (v.get("highlight") or "").lower().split(); size = 112
    while True:
        f = O(800, size); lines = wrap(d, text, f, 640)
        if (len(lines) <= 3 and yy + len(lines) * size * 1.05 < H - 120) or size <= 64: break
        size -= 6
    sp = d.textlength(" ", font=f)
    for ln in lines:
        xx = x0; pos = []
        for wd in ln.split():
            tw = d.textlength(wd, font=f); pos.append((wd, xx, tw, re.sub(r"[^\w']", "", wd.lower()) in hl)); xx += tw + sp
        k = 0
        while k < len(pos):  # one box around each run of highlighted words
            if pos[k][3]:
                j = k
                while j + 1 < len(pos) and pos[j + 1][3]: j += 1
                d.rounded_rectangle((pos[k][1] - 12, yy + size * 0.1, pos[j][1] + pos[j][2] + 12, yy + size * 1.08), radius=14, fill=(YEL if look == "a" else NAVY) + (255,))
                k = j
            k += 1
        for wd, xx, tw, on in pos:
            if not on: d.text((xx + 4, yy + 4), wd, font=f, fill=(0, 0, 0, 90))
            d.text((xx, yy), wd, font=f, fill=(NAVY if (on and look == "a") else WHITE))
        yy += size * 1.05
    lgi = logo(54, lg); im.alpha_composite(lgi, (x0, H - 54 - 44))
    im.convert("RGB").save(out, quality=90, optimize=True)


def cut_ok():
    try:
        import rembg  # noqa
        return True
    except Exception: return False


def main(spec, outdir, src=None, keep=None):
    th = spec.get("thumbnail") or {}
    if not th: return None
    src = src or clip.fetch(spec["source"], outdir); keep = keep or spec.get("keep") or [[0, clip.probe(src)["duration"]]]
    times = th.get("frames") or best_frames(src, keep)
    if len(times) == 1: times = times * 2
    for k, t in zip(("a", "b"), times):
        v = th.get(k) or th.get("a") or {"text": spec.get("title", "")}
        make(grab(src, t), v, k, os.path.join(outdir, f"thumb-{k}.jpg"))
    json.dump({"frames": times[:2], "cutout": cut_ok()}, open(os.path.join(outdir, "thumb-frames.json"), "w"))
    return times[:2]


if __name__ == "__main__":
    sp = clip.load(sys.argv[1]); os.makedirs(sys.argv[2], exist_ok=True); print(json.dumps({"frames": main(sp, sys.argv[2])}))
