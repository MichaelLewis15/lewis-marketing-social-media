"""Place Howie on an existing graphic in the calmest spot (lowest edge density), with a soft floor shadow."""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "howie")

def busy_map(im):
    g = np.asarray(im.convert("L").resize((im.width // 4, im.height // 4)), dtype=np.float32)
    gx = np.abs(np.diff(g, axis=1, prepend=g[:, :1])); gy = np.abs(np.diff(g, axis=0, prepend=g[:1, :]))
    e = ((gx + gy) > 18).astype(np.float32)
    # grow edges so thin text strokes count as a solid "keep out" area
    for _ in range(3):
        e = np.maximum.reduce([e, np.roll(e, 1, 0), np.roll(e, -1, 0), np.roll(e, 1, 1), np.roll(e, -1, 1)])
    return e, 4

def integral(a): return np.pad(a, ((1, 0), (1, 0))).cumsum(0).cumsum(1)

def box_sum(I, x0, y0, x1, y1): return I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0]

def place(src, out, frac=0.17, costume=None, pose=None, avoid=None, force=None, shadow=True):
    im = Image.open(src).convert("RGBA"); W, H = im.size
    h = int(H * frac) if H >= W else int(H * frac * 1.25)
    e, k = busy_map(im); I = integral(e)
    sp0 = Image.open(os.path.join(HERE, "howie-%s.png" % ((costume + "-" if costume else "") + (pose or ("cheer" if costume else "pointL"))))).convert("RGBA")
    w = int(sp0.width * h / sp0.height)
    best = None
    m = int(W * 0.02)
    xs = range(m, W - w - m, max(8, W // 60)); ys = range(int(H * 0.08), H - h - m, max(8, H // 60))
    for y in ys:
        for x in xs:
            pad = 6
            bx = (max(0, (x - pad) // k), max(0, (y - pad) // k), min(e.shape[1], (x + w + pad) // k), min(e.shape[0], (y + h + pad) // k))
            s = box_sum(I, bx[0], bx[1], bx[2], bx[3]) / ((bx[2] - bx[0]) * (bx[3] - bx[1]) + 1)
            # prefer lower part of the frame and the edges (less likely to sit on content)
            s = s + 0.04 * (1 - y / H) + 0.02 * (1 - abs((x + w / 2) / W - 0.5) * 2)
            if avoid and any(not (x + w < a[0] * W or x > a[2] * W or y + h < a[1] * H or y > a[3] * H) for a in avoid): continue
            if best is None or s < best[0]: best = (s, x, y)
    if force: best = (0, int(force[0] * W - w / 2), int(force[1] * H - h))
    _, x, y = best
    if not pose and not costume:
        pose = "pointL" if x + w / 2 > W * 0.55 else "pointR" if x + w / 2 < W * 0.45 else "wave"
    sp = Image.open(os.path.join(HERE, "howie-%s.png" % ((costume + "-" if costume else "") + (pose or "cheer")))).convert("RGBA")
    w = int(sp.width * h / sp.height); sp = sp.resize((w, h), Image.LANCZOS)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((x + w * .14, y + h - h * .035, x + w * .86, y + h + h * .035), fill=(10, 31, 68, 80))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(max(3, h // 40))))
    im.alpha_composite(sp, (x, y))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    (im.convert("RGB") if out.lower().endswith((".jpg", ".jpeg")) else im.convert("RGB")).save(out, quality=92) if out.lower().endswith((".jpg", ".jpeg")) else im.convert("RGB").save(out, optimize=True)
    return {"x": x, "y": y, "w": w, "h": h, "pose": pose, "costume": costume}

if __name__ == "__main__":
    a = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    print(json.dumps(place(sys.argv[1], sys.argv[2], **a)))
