"""Clip tool helpers: tightening (fillers, stutters, dead air), speaker-following crop, pop-up visuals."""
import re, math, subprocess, json
import numpy as np
from PIL import Image, ImageDraw

FILLERS = {"um", "umm", "uh", "uhh", "uh-huh", "er", "erm", "ah", "ahh", "hmm", "hm", "mm", "mhm"}


def _norm(w):
    return re.sub(r"[^a-z'-]", "", w.lower())


# ------------------------------------------------------------------ 3. tighten
def tighten(words, keep, max_pause=0.45, pad=0.08):
    """Remove filler words, stutters (the same word twice in a row) and pauses longer than max_pause from the
    kept parts. words: [[w, start, end], ...] on the SOURCE timeline. Returns new keep ranges and what was cut."""
    out, cut = [], {"fillers": 0, "stutters": 0, "pauses": 0, "seconds": 0.0}
    for a, b in keep:
        ws = [w for w in words if w[1] >= a - 0.05 and w[2] <= b + 0.15]
        if not ws: out.append([a, b]); continue
        good = []
        for i, w in enumerate(ws):
            n = _norm(w[0])
            if n in FILLERS: cut["fillers"] += 1; continue
            nxt = ws[i + 1] if i + 1 < len(ws) else None
            if nxt and _norm(nxt[0]) == n and n and nxt[1] - w[2] < 0.6 and n not in ("that", "had", "very", "really", "no", "yes", "bye"):
                cut["stutters"] += 1; continue
            good.append(w)
        if not good: continue
        seg = [max(a, good[0][1] - pad), None]
        for w0, w1 in zip(good, good[1:]):
            gap = w1[1] - w0[2]
            dropped_between = any(x[1] >= w0[2] - 0.01 and x[2] <= w1[1] + 0.01 for x in ws if x not in good)
            if gap > max_pause or dropped_between:
                seg[1] = w0[2] + pad; out.append(seg); seg = [w1[1] - pad, None]
                if gap > max_pause: cut["pauses"] += 1
        seg[1] = min(b, good[-1][2] + pad * 2); out.append(seg)
    merged = []
    for s in out:
        if merged and s[0] - merged[-1][1] < 0.06: merged[-1][1] = max(merged[-1][1], s[1])
        else: merged.append([round(s[0], 3), round(s[1], 3)])
    merged = [s for s in merged if s[1] - s[0] >= 0.2]
    cut["seconds"] = round(sum(b - a for a, b in keep) - sum(b - a for a, b in merged), 2)
    return merged, cut


# ------------------------------------------------------------------ 2. follow the speaker
def face_cascade():
    """OpenCV's frontal-face detector; the XML ships in this folder (newer OpenCV wheels no longer include it)"""
    import cv2, os
    for p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "haarcascade_frontalface_default.xml"),
              os.path.join(getattr(getattr(cv2, "data", None), "haarcascades", ""), "haarcascade_frontalface_default.xml")):
        if os.path.exists(p):
            c = cv2.CascadeClassifier(p)
            if not c.empty(): return c
    raise RuntimeError("face detector not found")


def follow_track(video, fps=5, width=640):
    """Find the faces in the (already cut) video and decide who is talking, from mouth movement while there is
    sound. Returns [(t_start, x_center 0-1), ...] for a vertical crop that switches to the speaker."""
    import cv2
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", video],
                                   capture_output=True, text=True, check=True).stdout)["streams"][0]
    h = int(round(pr["height"] * width / pr["width"] / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={width}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, h, width)
    aud = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(aud, np.int16).astype(float); per = 8000 // fps
    loud = np.array([np.sqrt(np.mean(a[i * per:(i + 1) * per] ** 2)) if i * per < len(a) else 0 for i in range(len(frames))])
    voiced = loud > max(300, np.percentile(loud, 40))
    cas = face_cascade()
    dets = []
    for i, f in enumerate(frames):
        for (x, y, w, hh) in cas.detectMultiScale(f, 1.1, 5, minSize=(int(width * 0.06), int(width * 0.06))):
            dets.append((i, (x + w / 2) / width, x, y, w, hh))
    if not dets: return [(0.0, 0.5)]
    xs = sorted(d[1] for d in dets); groups = [[xs[0]]]
    for v in xs[1:]:
        (groups[-1].append(v) if v - groups[-1][-1] < 0.12 else groups.append([v]))
    groups = [g for g in groups if len(g) >= max(3, 0.12 * len(frames))]
    if not groups: return [(0.0, float(np.median(xs)))]
    centers = [float(np.median(g)) for g in groups]
    if len(centers) == 1: return [(0.0, centers[0])]
    score = np.zeros((len(frames), len(centers)))
    seen = np.zeros((len(frames), len(centers)))
    for i, cxn, x, y, w, hh in dets:
        k = int(np.argmin([abs(cxn - c) for c in centers]))
        if abs(cxn - centers[k]) > 0.12: continue
        seen[i, k] = 1
        if i == 0: continue
        y0, y1 = int(y + hh * 0.62), int(y + hh * 0.98); x0, x1 = int(x + w * 0.25), int(x + w * 0.75)
        roi1 = frames[i, y0:y1, x0:x1].astype(float); roi0 = frames[i - 1, y0:y1, x0:x1].astype(float)
        if roi1.size: score[i, k] = max(score[i, k], np.mean(np.abs(roi1 - roi0)))
    win = max(1, int(0.8 * fps)); timeline = []; cur = None; since = 0
    for i in range(0, len(frames), max(1, fps // 2)):
        s = score[max(0, i - win):i + win].mean(0) * (1 if voiced[max(0, i - win):i + win].any() else 0)
        vis = seen[max(0, i - win):i + win].mean(0)
        if vis.max() == 0: continue
        cand = int(np.argmax(s + vis * 0.01)) if s.max() > 0 else (cur if cur is not None and vis[cur] > 0 else int(np.argmax(vis)))
        if vis.sum() and (vis > 0).sum() == 1: cand = int(np.argmax(vis))  # only one face on screen: show it
        t = i / fps
        if cur is None: cur = cand; since = t; timeline.append((0.0, centers[cur])); continue
        if cand != cur and t - since >= 1.5 and (s[cand] > s[cur] * 1.3 or vis[cur] == 0):
            cur = cand; since = t; timeline.append((round(t - 0.2, 2), centers[cur]))
    return timeline or [(0.0, centers[0])]


def crop_expr(timeline, iw, W):
    """ffmpeg crop x expression for the timeline (instant cuts between speakers)"""
    def px(c): return int(max(0, min(iw - W, c * iw - W / 2)))
    e = str(px(timeline[-1][1]))
    for (t0, c), (t1, _) in reversed(list(zip(timeline, timeline[1:]))):
        e = f"if(lt(t\\,{t1:.2f})\\,{px(c)}\\,{e})"
    return e


# ------------------------------------------------------------------ 4. pop-up visuals
TOPICS = [  # (regex on the spoken words, kind, label)
    (r"\bgoogle reviews?\b|\breviews?\b|\bfive[- ]star\b|\b5[- ]star\b", "reviews", "Reviews"),
    (r"\bwebsites?\b|\bweb ?page\b|\blanding page\b|\bhome ?page\b", "website", "Your website"),
    (r"\bhigh ?level\b|\bcrm\b|\bpipeline\b|\bautomation\b|\bworkflow", "crm", "CRM and automation"),
    (r"\btext(ing|s|ed)?\b|\bsms\b|\bmissed call", "text", "Text back"),
    (r"\bemails?\b|\bnewsletter", "email", "Email"),
    (r"\bgoogle\b|\bsearch\b|\bseo\b|\bmaps\b", "search", "Found on Google"),
    (r"\bads?\b|\badvertis|\bboost(ed)?\b", "ads", "Advertising"),
    (r"\bfacebook\b|\binstagram\b|\btiktok\b|\bsocial media\b|\byoutube\b", "social", "Social media"),
    (r"\bchat ?gpt\b|\bai\b|\bartificial intelligence\b", "ai", "AI tools"),
    (r"\bcalls?\b|\bphone\b|\bcall(ed|ing)? (us|back)\b", "phone", "Phone calls"),
    (r"\bbook(ing|ed)?\b|\bappointments?\b|\bschedul", "calendar", "Online booking"),
]


def auto_popups(words, busy, max_n=4, gap=6.0, start=1.5):
    """words on the output timeline -> [{"at", "kind", "label"}] at the first mention of a topic, spaced out and
    kept away from busy windows (lower third, cards, end)"""
    text, idx = "", []
    for k, w in enumerate(words):
        idx.append((len(text), k)); text += re.sub(r"[^\w' -]", "", w[0].lower()) + " "
    hits, used = [], set()
    for rx, kind, label in TOPICS:
        for m in re.finditer(rx, text):
            k = max(i for pos, i in idx if pos <= m.start()); t = words[k][1]
            hits.append((t, kind, label)); break
    hits.sort(); out = []
    for t, kind, label in hits:
        if kind in used or t < start or any(a - 0.5 <= t <= b + 0.5 for a, b in busy): continue
        if out and t - out[-1]["at"] < gap: continue
        out.append({"at": round(t, 2), "kind": kind, "label": label, "dur": 2.6}); used.add(kind)
        if len(out) >= max_n: break
    return out


def icon(kind, s, navy=(10, 31, 68), sky=(41, 162, 222), yel=(244, 197, 66)):
    """simple drawn icons (no third-party logos)"""
    im = Image.new("RGBA", (s, s)); d = ImageDraw.Draw(im); lw = max(3, s // 18)
    if kind == "reviews":
        for k in range(5):
            cx = s * (0.12 + k * 0.19); cy = s * 0.5; r = s * 0.09
            pts = [(cx + (r if j % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + j * math.pi / 5), cy + (r if j % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + j * math.pi / 5)) for j in range(10)]
            d.polygon(pts, fill=yel)
    elif kind == "website":
        d.rounded_rectangle((s * .08, s * .18, s * .92, s * .82), radius=s // 14, outline=navy, width=lw)
        d.line((s * .08, s * .34, s * .92, s * .34), fill=navy, width=lw)
        for k in range(3): d.ellipse((s * (.14 + k * .07), s * .23, s * (.18 + k * .07), s * .29), fill=sky)
        d.rectangle((s * .18, s * .44, s * .6, s * .52), fill=sky); d.rectangle((s * .18, s * .6, s * .8, s * .64), fill=navy); d.rectangle((s * .18, s * .7, s * .7, s * .74), fill=navy)
    elif kind == "crm":
        for k, hh in enumerate((.3, .5, .42, .66)):
            x = s * (.14 + k * .19); d.rounded_rectangle((x, s * (.82 - hh), x + s * .13, s * .82), radius=s // 40, fill=sky if k % 2 else navy)
        d.line((s * .1, s * .84, s * .9, s * .84), fill=navy, width=lw)
    elif kind == "text":
        d.rounded_rectangle((s * .1, s * .2, s * .78, s * .58), radius=s // 9, fill=sky); d.polygon([(s * .2, s * .56), (s * .3, s * .56), (s * .16, s * .7)], fill=sky)
        d.rounded_rectangle((s * .3, s * .5, s * .92, s * .82), radius=s // 10, fill=navy)
        for k in range(3): d.ellipse((s * (.5 + k * .1), s * .63, s * (.55 + k * .1), s * .68), fill=(255, 255, 255))
    elif kind == "email":
        d.rounded_rectangle((s * .1, s * .25, s * .9, s * .78), radius=s // 16, outline=navy, width=lw)
        d.line([(s * .12, s * .28), (s * .5, s * .56), (s * .88, s * .28)], fill=sky, width=lw, joint="curve")
    elif kind == "search":
        d.rounded_rectangle((s * .06, s * .36, s * .94, s * .64), radius=int(s * .14), outline=navy, width=lw)
        d.ellipse((s * .13, s * .41, s * .29, s * .57), outline=sky, width=lw); d.line((s * .27, s * .55, s * .33, s * .61), fill=sky, width=lw)
        d.rectangle((s * .38, s * .47, s * .8, s * .53), fill=navy)
    elif kind == "ads":
        d.polygon([(s * .14, s * .4), (s * .42, s * .4), (s * .78, s * .2), (s * .78, s * .8), (s * .42, s * .6), (s * .14, s * .6)], fill=navy)
        d.rectangle((s * .26, s * .6, s * .38, s * .8), fill=sky)
        for k in range(3): d.line((s * .84, s * (.38 + k * .12), s * .94, s * (.33 + k * .17)), fill=yel, width=lw)
    elif kind == "social":
        d.ellipse((s * .14, s * .22, s * .5, s * .58), fill=sky); d.ellipse((s * .5, s * .22, s * .86, s * .58), fill=sky)
        d.polygon([(s * .16, s * .46), (s * .84, s * .46), (s * .5, s * .84)], fill=sky)
    elif kind == "ai":
        d.rounded_rectangle((s * .1, s * .2, s * .9, s * .7), radius=s // 8, fill=navy); d.polygon([(s * .3, s * .68), (s * .44, s * .68), (s * .26, s * .84)], fill=navy)
        from PIL import ImageFont
        try:
            import os; f = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "..", "howie-tools", "outfit-latin-800-normal.woff"), int(s * .26))
            d.text((s * .5, s * .45), "AI", font=f, fill=(255, 255, 255), anchor="mm")
        except Exception: pass
        d.polygon([(s * .82, s * .08), (s * .86, s * .18), (s * .96, s * .22), (s * .86, s * .26), (s * .82, s * .36), (s * .78, s * .26), (s * .68, s * .22), (s * .78, s * .18)], fill=yel)
    elif kind == "phone":
        d.rounded_rectangle((s * .3, s * .08, s * .7, s * .92), radius=s // 12, outline=navy, width=lw)
        d.rectangle((s * .42, s * .14, s * .58, s * .17), fill=navy); d.ellipse((s * .46, s * .8, s * .54, s * .88), outline=navy, width=lw // 2 + 1)
        for k in range(2): d.arc((s * (.62 + k * .08), s * (.2 - k * .05), s * (.86 + k * .08), s * (.44 + k * .05)), 300, 60, fill=sky, width=lw)
    elif kind == "calendar":
        d.rounded_rectangle((s * .12, s * .18, s * .88, s * .86), radius=s // 14, outline=navy, width=lw); d.rectangle((s * .12, s * .18, s * .88, s * .34), fill=sky)
        for r in range(3):
            for c in range(4): d.rectangle((s * (.2 + c * .17), s * (.42 + r * .13), s * (.29 + c * .17), s * (.49 + r * .13)), fill=yel if (r, c) == (1, 2) else navy)
    return im
