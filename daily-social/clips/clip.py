"""Lewis Marketing clip tool: turns real footage into finished social videos.

Two jobs, one renderer:
  * clips from long recordings (Behind the Storefront, The Marketing Lens, webinars): pick a 20-75 second moment,
    lay the 16:9 footage into a branded 9:16 frame with the hook on top and big captions below, plus a 16:9 cut;
  * talking-head polish for Michael's phone videos: trim the flubs, burn in captions, add his name and title,
    text cards on the key points, an end card with the call to action and an optional quiet music bed.

usage:
  python3 clip.py transcribe SOURCE OUT.json [--model small.en]     words with timestamps (+ OUT.txt, readable)
  python3 clip.py render SPEC.json OUTDIR                             finished videos
  python3 clip.py preview SPEC.json OUTDIR                            a few stills, no video

SPEC keys (times in seconds of the SOURCE unless noted):
  source       path or URL of the footage            transcript   path of the transcribe JSON (captions)
  keep         [[start, end], ...] parts to keep, in order (cuts out flubs and pauses); default the whole source
  layout       "auto" (default: fit for landscape footage, full for portrait), "fit", "full"; cropX 0-1 for full
  style        "navy" (default) | "light" | "bold": frame colors for the fit layout and cards
  eyebrow      small label on top (fit), e.g. "BEHIND THE STOREFRONT";   title  the hook, shown on top (fit) or
               for the first 3 seconds (full)
  lowerThird   {"name", "role", "at" (output s, default 0.4), "dur" (default 3.5)}; e.g. guest or Michael
  cards        [{"at": output s, "dur": 3, "text": "..."}]  key points as text cards
  captions     true (default)
  endCard      {"cta", "cta2", "button", "dur" (2.8)} or false;  music  null or 0-3 (quiet bed under the voice)
  sizes        ["916"] plus "169" for landscape footage (default both when the footage is landscape), "45" optional
Outputs: v<size>.mp4, cover<size>.jpg, captions.srt.
"""
import json, os, re, sys, subprocess, tempfile, math, hashlib, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "howie-tools"); ENGINE = os.path.join(HERE, "..", "engine")
MODELS = os.environ.get("LM_MODELS", os.path.join(HERE, "..", "models"))
sys.path.insert(0, TOOLS)
FPS = 30
NAVY = (10, 31, 68); NAVY2 = (5, 16, 38); SKY = (41, 162, 222); BLUE = (4, 107, 210); YEL = (244, 197, 66)
WHITE = (255, 255, 255); MIST = (200, 214, 230); CREAM = (247, 244, 237); SLATE = (74, 90, 115)
_F = {}


def O(w, s):
    k = ("o", w, int(s))
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(TOOLS, f"outfit-latin-{w}-normal.woff"), int(s))
    return _F[k]


def S(w, s):
    k = ("s", w, int(s))
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(TOOLS, f"open-sans-latin-{w}-normal.woff"), int(s))
    return _F[k]


def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def wrap(d, text, font, width):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def logo(h, kind="white"):
    """kind: color (light backgrounds), white (two-tone white logo, navy backgrounds), allwhite (blue backgrounds)"""
    src = Image.open(os.path.join(ENGINE, "logo.png" if kind == "color" else "logo_white.png")).convert("RGBA")
    if kind == "allwhite": w = Image.new("RGBA", src.size, WHITE + (255,)); w.putalpha(src.getchannel("A")); src = w
    return src.resize((int(src.width * h / src.height), h), Image.LANCZOS)


def run(*a, **k):
    return subprocess.run(list(a), check=True, **k)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_side_data=rotation:format=duration",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out); st = (j.get("streams") or [{}])[0]; w, h = st.get("width"), st.get("height")
    rot = 0
    for sd in st.get("side_data_list") or []:
        if "rotation" in sd: rot = int(sd["rotation"])
    if abs(rot) in (90, 270): w, h = h, w
    return dict(width=w, height=h, duration=float(j["format"]["duration"]))


CACHE = os.environ.get("CLIP_CACHE", os.path.join(os.environ.get("TMPDIR", "/tmp"), "clip-cache"))


def fetch(src, tmp):
    if re.match(r"https?://", src):
        os.makedirs(CACHE, exist_ok=True); tmp = CACHE
        p = os.path.join(tmp, "src-" + hashlib.sha1(src.encode()).hexdigest()[:10] + os.path.splitext(src.split("?")[0])[1])
        if not os.path.exists(p): urllib.request.urlretrieve(src, p)
        return p
    return src


# ------------------------------------------------------------------ transcribe
def transcribe(src, out, model=None):
    from faster_whisper import WhisperModel
    tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR", "/tmp")); src_l = fetch(src, tmp); info = probe(src_l)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src_l, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    local = os.path.join(MODELS, "whisper-tiny.en")
    name = model or os.environ.get("LM_WHISPER") or "small.en"
    try: m = WhisperModel(name, device="cpu", compute_type="int8")
    except Exception: m = WhisperModel(local, device="cpu", compute_type="int8"); name = "tiny.en (local)"
    segs, _ = m.transcribe(audio, word_timestamps=True, vad_filter=True, beam_size=5, language="en")
    S_ = []
    for s in segs:
        S_.append(dict(start=round(s.start, 2), end=round(s.end, 2), text=s.text.strip(), words=[[w.word.strip(), round(w.start, 2), round(w.end, 2)] for w in s.words]))
    res = dict(source=src, model=name, **info, segments=S_)
    json.dump(res, open(out, "w"), indent=0)
    with open(os.path.splitext(out)[0] + ".txt", "w") as f:
        for s in S_: f.write(f"[{int(s['start'] // 60):02d}:{s['start'] % 60:05.2f} - {int(s['end'] // 60):02d}:{s['end'] % 60:05.2f}] {s['text']}\n")
    print(json.dumps({"segments": len(S_), "duration": info["duration"], "model": name, "out": out}))


# ------------------------------------------------------------------ helpers for the output timeline
def kept_words(tr, keep):
    """words inside the kept parts, shifted onto the output timeline"""
    out, off = [], 0.0
    words = [w for s in tr["segments"] for w in s["words"]]
    for a, b in keep:
        for w, s, e in words:
            if s >= a - 0.05 and e <= b + 0.15: out.append((w, off + max(0, s - a), off + min(b, e) - a))
        off += b - a
    return out


def chunks(d, words, font, maxw):
    res, a = [], 0
    while a < len(words):
        b = a
        while b + 1 < len(words) and words[b + 1][1] - words[b][2] < 0.7 and d.textlength(" ".join(w[0] for w in words[a:b + 2]), font=font) <= maxw \
                and not re.search(r"[.!?]$", words[b][0]) and b - a < 5:
            b += 1
        res.append((a, b)); a = b + 1
    return res


def srt(words, chs, path):
    def ts(t): return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int((t % 1) * 1000):03d}"
    with open(path, "w") as f:
        for k, (a, b) in enumerate(chs):
            f.write(f"{k + 1}\n{ts(words[a][1])} --> {ts(words[b][2] + 0.2)}\n{' '.join(w[0] for w in words[a:b + 1])}\n\n")


# ------------------------------------------------------------------ geometry per size
PAL = {"navy": dict(bg1=NAVY, bg2=NAVY2, ink=WHITE, ink2=MIST, acc=YEL, eyebrow=SKY, logo="white"),
       "light": dict(bg1=CREAM, bg2=(236, 231, 220), ink=NAVY, ink2=SLATE, acc=BLUE, eyebrow=NAVY, logo="color"),
       "bold": dict(bg1=BLUE, bg2=(3, 84, 168), ink=WHITE, ink2=(214, 228, 245), acc=YEL, eyebrow=NAVY, logo="allwhite")}


class Geo:
    def __init__(self, key, layout, sw, sh):
        self.key = key; self.layout = layout
        self.W, self.H = {"916": (1080, 1920), "169": (1920, 1080), "45": (1080, 1350)}[key]
        W, H = self.W, self.H
        if key == "169":
            self.vid = (0, 0, W, H); self.cap_y = 905; self.cap_w = 1500; self.cap_f = 52; self.lt = (70, 760); self.card_y = 120
        elif layout == "fit":
            vw = W; vh = int(round(vw * sh / sw / 2) * 2)
            top = 560 if key == "916" else 330
            self.vid = (0, top, vw, vh); self.cap_y = top + vh + 70; self.cap_w = 960; self.cap_f = 64 if key == "916" else 52
            self.lt = (50, top + vh - 190); self.card_y = top + 30
        else:  # full frame (portrait footage, or cropped)
            self.vid = (0, 0, W, H); self.cap_y = int(H * 0.66); self.cap_w = 960; self.cap_f = 66 if key == "916" else 54
            self.lt = (50, int(H * 0.78)); self.card_y = int(H * 0.14)


def static_frame(g, spec, pal):
    """background for the fit layout: brand colors, eyebrow, hook, footer logo"""
    W, H = g.W, g.H; im = Image.new("RGBA", (W, H))
    if g.layout != "fit" or g.key == "169": return im
    y = np.linspace(0, 1, H)[:, None, None]
    arr = np.array(pal["bg1"], float) * (1 - y) + np.array(pal["bg2"], float) * y
    im = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im)
    x0 = 70; top = g.vid[1]; yy = 110 if g.key == "916" else 50
    if spec.get("eyebrow"):
        f = S(600, 30); tw = d.textlength(spec["eyebrow"], font=f); h = 52
        d.rounded_rectangle((x0, yy, x0 + tw + 44, yy + h), radius=26, fill=pal["eyebrow"]); d.text((x0 + 22, yy + h / 2), spec["eyebrow"], font=f, fill=WHITE, anchor="lm")
        yy += h + 28
    if spec.get("title"):
        size = 76 if g.key == "916" else 56; f = O(800, size)
        lines = wrap(d, spec["title"], f, W - 2 * x0)
        while (len(lines) > 3 or yy + len(lines) * size * 1.08 > top - 30) and size > 44:
            size -= 4; f = O(800, size); lines = wrap(d, spec["title"], f, W - 2 * x0)
        for ln in lines: d.text((x0, yy), ln, font=f, fill=pal["ink"]); yy += size * 1.08
    lg = logo(60 if g.key == "916" else 48, pal["logo"])
    ly = H - 150 if g.key == "916" else H - 90
    im.alpha_composite(lg, ((W - lg.width) // 2, ly))
    if g.key == "916": d.text((W / 2, ly + 92), "lewismarketingoc.com", font=S(600, 28), fill=pal["ink2"], anchor="mm")
    return im


class Overlay:
    def __init__(self, g, spec, pal, words, total, body):
        self.g, self.spec, self.pal, self.words, self.total, self.body = g, spec, pal, words, total, body
        d = ImageDraw.Draw(Image.new("RGB", (8, 8))); self.cf = O(800, g.cap_f)
        self.chs = chunks(d, words, self.cf, g.cap_w - g.cap_f) if spec.get("captions", True) else []
        self._cache = {}

    def state(self, t):
        sp = self.spec; k = []
        if t >= self.body:  # end card
            return ("end", min(10, int((t - self.body) * FPS)))
        cur = None
        if self.chs:
            idx = [i for i, w in enumerate(self.words) if w[1] - 0.05 <= t <= w[2] + 0.3]
            if idx:
                i = idx[-1]; cur = next(((a, b, i) for a, b in self.chs if a <= i <= b), None)
        k.append(cur)
        lt = sp.get("lowerThird")
        if lt:
            a = lt.get("at", 0.4); dur = lt.get("dur", 3.5)
            if a <= t < a + dur: k.append(("lt", min(8, int((t - a) * FPS)), max(0, int((t - (a + dur - 0.3)) * FPS))))
        for j, c in enumerate(sp.get("cards") or []):
            dt = t - c["at"]
            if 0 <= dt < c.get("dur", 3): k.append(("card", j, min(8, int(dt * FPS)), max(0, int((dt - c.get("dur", 3) + 0.25) * FPS))))
        if self.g.layout == "full" and sp.get("title") and t < 3.2: k.append(("hook", min(8, int(t * FPS)), max(0, int((t - 2.9) * FPS))))
        return tuple(k)

    def frame(self, t):
        st = self.state(t)
        if st in self._cache: return self._cache[st]
        g, pal = self.g, self.pal; W, H = g.W, g.H; im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
        if st[0] == "end":
            self.endcard(im, d, st[1] / 10); b = im.tobytes(); self._cache[st] = b; return b
        for item in st:
            if item is None: continue
            if isinstance(item, tuple) and len(item) == 3 and isinstance(item[0], int):
                a, b_, i = item; toks = [w[0] for w in self.words[a:b_ + 1]]
                lines, line = [], []
                for j, tk in enumerate(toks):
                    test = " ".join(x for x, _ in line + [(tk, 0)])
                    if line and d.textlength(test, font=self.cf) > g.cap_w - g.cap_f: lines.append(line); line = []
                    line.append((tk, a + j))
                lines.append(line)
                y = g.cap_y; lh = g.cap_f * 1.22
                for ln in lines:
                    txt = " ".join(x for x, _ in ln); tw = d.textlength(txt, font=self.cf); x = (W - tw) / 2
                    pad = g.cap_f * 0.35
                    d.rounded_rectangle((x - pad, y - pad * 0.6, x + tw + pad, y + g.cap_f * 1.05 + pad * 0.6), radius=int(pad), fill=NAVY2 + (215,))
                    for tk, wi in ln:
                        d.text((x, y), tk, font=self.cf, fill=YEL if wi == i else WHITE); x += d.textlength(tk + " ", font=self.cf)
                    y += lh + pad
            elif item[0] == "lt":
                k_in, k_out = item[1], item[2]
                lt = self.spec["lowerThird"]; a = ease(k_in / 8) * (1 - ease(k_out / 9))
                x, y = g.lt; fn, fr = O(800, 44 if W < 1500 else 40), S(600, 30 if W < 1500 else 26)
                w = max(d.textlength(lt.get("name", ""), font=fn), d.textlength(lt.get("role", ""), font=fr)) + 70
                L = Image.new("RGBA", (W, H)); ld = ImageDraw.Draw(L)
                ld.rounded_rectangle((x, y, x + w, y + 130), radius=18, fill=WHITE + (245,)); ld.rectangle((x, y + 18, x + 10, y + 112), fill=SKY)
                ld.text((x + 32, y + 22), lt.get("name", ""), font=fn, fill=NAVY); ld.text((x + 32, y + 78), lt.get("role", ""), font=fr, fill=SLATE)
                L = L.transform(L.size, Image.AFFINE, (1, 0, int((1 - a) * 80), 0, 1, 0))
                L.putalpha(L.getchannel("A").point(lambda v: int(v * a))); im.alpha_composite(L)
            elif item[0] == "card":
                c = self.spec["cards"][item[1]]; a = ease(item[2] / 8) * (1 - ease(item[3] / 8))
                f = O(800, 58 if W < 1500 else 52); maxw = (W - 160) if W < 1500 else 1100
                lines = wrap(d, c["text"], f, maxw - 80); h = len(lines) * f.size * 1.15 + 70; cw = max(d.textlength(l, font=f) for l in lines) + 80
                x = (W - cw) / 2; y = g.card_y
                L = Image.new("RGBA", (W, H)); ld = ImageDraw.Draw(L)
                ld.rounded_rectangle((x, y, x + cw, y + h), radius=26, fill=WHITE + (248,)); ld.rectangle((x + 30, y + h - 14, x + 130, y + h - 6), fill=YEL)
                yy = y + 30
                for l in lines: ld.text((W / 2, yy), l, font=f, fill=NAVY, anchor="ma"); yy += f.size * 1.15
                L = L.transform(L.size, Image.AFFINE, (1, 0, 0, 0, 1, int((1 - a) * -40)))
                L.putalpha(L.getchannel("A").point(lambda v: int(v * a))); im.alpha_composite(L)
            elif item[0] == "hook":
                a = ease(item[1] / 8) * (1 - ease(item[2] / 9)); f = O(800, 70 if W < 1500 else 60)
                lines = wrap(d, self.spec["title"], f, W - 200); h = len(lines) * f.size * 1.12 + 60
                L = Image.new("RGBA", (W, H)); ld = ImageDraw.Draw(L); y = g.card_y
                cw = max(ld.textlength(l, font=f) for l in lines) + 70; x = (W - cw) / 2
                ld.rounded_rectangle((x, y, x + cw, y + h), radius=24, fill=NAVY + (235,)); yy = y + 30
                for l in lines: ld.text((W / 2, yy), l, font=f, fill=WHITE, anchor="ma"); yy += f.size * 1.12
                L.putalpha(L.getchannel("A").point(lambda v: int(v * a))); im.alpha_composite(L)
        if g.layout == "full" or g.key == "169":  # small logo bug
            lg = self._bug if hasattr(self, "_bug") else logo(44 if W < 1500 else 40)
            self._bug = lg; im.alpha_composite(lg, (W - lg.width - 40, 40))
        b = im.tobytes(); self._cache[st] = b; return b

    def endcard(self, im, d, k):
        g, pal = self.g, self.pal; W, H = g.W, g.H; e = self.spec.get("endCard") or {}
        bg = Image.new("RGBA", (W, H), NAVY + (int(255 * ease(k * 1.5)),)); im.alpha_composite(bg)
        lg = logo(90 if W < 1500 else 80); cy = H * 0.3
        im.alpha_composite(lg, ((W - lg.width) // 2, int(cy)))
        y = cy + 170; f = O(800, 72 if W < 1500 else 64)
        for l in wrap(d, e.get("cta", "Want help with your marketing?"), f, W - 180): d.text((W / 2, y), l, font=f, fill=WHITE, anchor="ma"); y += f.size * 1.12
        if e.get("cta2"):
            f2 = O(700, 44); y += 10
            for l in wrap(d, e["cta2"], f2, W - 200): d.text((W / 2, y), l, font=f2, fill=YEL, anchor="ma"); y += 56
        y += 40; fb = S(600, 36); txt = e.get("button", "Book a call: lewismarketingoc.com"); tw = d.textlength(txt, font=fb)
        d.rounded_rectangle((W / 2 - tw / 2 - 30, y, W / 2 + tw / 2 + 30, y + 74), radius=37, fill=SKY); d.text((W / 2, y + 37), txt, font=fb, fill=WHITE, anchor="mm")
        if e.get("howie", True):
            hp = Image.open(os.path.join(TOOLS, "howie", "howie-wave.png")).convert("RGBA"); hh = 300 if W < 1500 else 260
            hp = hp.resize((int(hp.width * hh / hp.height), hh), Image.LANCZOS); im.alpha_composite(hp, ((W - hp.width) // 2, int(H - hh - (150 if W < 1500 else 60))))


# ------------------------------------------------------------------ render
def build_cut(src, keep, tmp, total_src):
    """trim the kept parts out of the source and join them (constant 30 fps, 48 kHz)"""
    parts = []
    for n, (a, b) in enumerate(keep):
        p = os.path.join(tmp, f"part{n}.mp4")
        run("ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", src, "-t", f"{b - a:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k", "-af", "afade=t=in:d=0.04,afade=t=out:st=%.3f:d=0.05" % max(0, b - a - 0.05), p)
        parts.append(p)
    lst = os.path.join(tmp, "parts.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    out = os.path.join(tmp, "cut.mp4"); run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out)
    return out


def render_size(g, spec, pal, cut, words, body, total, tmp, out, music_wav):
    W, H = g.W, g.H; x, y, vw, vh = g.vid
    st = static_frame(g, spec, pal); stp = os.path.join(tmp, f"static{g.key}.png"); st.save(stp)
    if g.layout == "full" and g.key != "169":
        cx = spec.get("cropX", 0.5)
        vf = f"[1:v]scale=-2:{H},crop={W}:{H}:'max(0,min(iw-{W},iw*{cx}-{W}/2))':0,setsar=1[v]"
    else:
        vf = f"[1:v]scale={vw}:{vh},setsar=1[v]"
    ov = Overlay(g, spec, pal, words, total, body)
    fc = (f"[0:v]loop=-1:1:0,trim=duration={total:.3f},fps={FPS}[bg];{vf};[v]tpad=stop_mode=clone:stop_duration={total - body + 0.5:.3f}[vv];"
          f"[bg][vv]overlay={x}:{y}:shortest=0[base];[2:v]format=rgba[ol];[base][ol]overlay=0:0:format=auto,format=yuv420p,trim=duration={total:.3f}[outv]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", stp, "-i", cut, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", music_wav, "-filter_complex", fc + ";[3:a]atrim=duration=%.3f[aout]" % total, "-map", "[outv]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(round(total * FPS))): p.stdin.write(ov.frame(f / FPS))
    p.stdin.close(); p.wait()
    if p.returncode: raise SystemExit("ffmpeg failed for " + g.key)
    return ov


def mix_audio(cut, body, total, spec, tmp):
    """speech loudness-normalised, optional quiet music bed, music carries the end card"""
    out = os.path.join(tmp, "mix.wav"); m = spec.get("music")
    speech = os.path.join(tmp, "speech.wav")
    run("ffmpeg", "-v", "error", "-y", "-i", cut, "-vn", "-af", "highpass=f=70,loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", speech)
    if m is None:
        run("ffmpeg", "-v", "error", "-y", "-i", speech, "-af", f"apad=whole_dur={total:.3f}", out); return out
    import music
    mw = os.path.join(tmp, "music.wav"); music.render(total + 0.5, mw, int(m))
    run("ffmpeg", "-v", "error", "-y", "-i", speech, "-i", mw, "-filter_complex",
        f"[1:a]aresample=48000,volume='if(lt(t,{body:.2f}),0.10,0.55)':eval=frame,afade=t=out:st={total - 1.2:.2f}:d=1.2[m];[0:a]apad=whole_dur={total:.3f}[s];[s][m]amix=inputs=2:normalize=0:duration=first[o]",
        "-map", "[o]", out)
    return out


def load(spec_path):
    spec = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    root = os.path.abspath(os.path.join(HERE, "..", ".."))
    for k in ("source", "transcript"):
        v = spec.get(k)
        if v and not re.match(r"https?://", v) and not os.path.isabs(v):
            spec[k] = v if os.path.exists(v) else os.path.join(root, v)
    return spec


def main(spec_path, outdir, preview_only=False):
    spec = load(spec_path); os.makedirs(outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR", "/tmp")); src = fetch(spec["source"], tmp); info = probe(src)
    keep = spec.get("keep") or [[0, info["duration"]]]
    keep = [[max(0, a), min(info["duration"], b)] for a, b in keep]
    body = sum(b - a for a, b in keep); end = spec.get("endCard", {}) ; ed = (end or {}).get("dur", 2.8) if end is not False else 0
    total = body + ed
    landscape = info["width"] > info["height"]; layout = spec.get("layout", "auto")
    layout = ("fit" if landscape else "full") if layout == "auto" else layout
    sizes = spec.get("sizes") or (["916", "169"] if landscape else ["916"])
    tr = json.load(open(spec["transcript"])) if spec.get("transcript") else {"segments": []}
    words = kept_words(tr, keep); pal = PAL[spec.get("style", "navy")]
    if preview_only:
        for key in sizes:
            g = Geo(key, "fit" if (key != "169" and layout == "fit") else ("full" if key != "169" else "fit"), info["width"], info["height"])
            st = static_frame(g, spec, pal); ov = Overlay(g, spec, pal, words, total, body)
            for t in [0.5, 2.0, body * 0.5, max(0, body - 1), body + ed - 0.3]:
                fr = Image.new("RGBA", (g.W, g.H), (40, 40, 40, 255)); fr.alpha_composite(st)
                lay = Image.frombytes("RGBA", (g.W, g.H), ov.frame(t))
                fr.alpha_composite(lay); fr.convert("RGB").save(f"{outdir}/{key}-{t:05.1f}.jpg", quality=85)
        return
    cut = build_cut(src, keep, tmp, info["duration"]); mix = mix_audio(cut, body, total, spec, tmp)
    for key in sizes:
        lay = "fit" if (key != "169" and layout == "fit") else ("full" if key != "169" else "fit")
        if key == "169" and not landscape: continue
        g = Geo(key, lay, info["width"], info["height"])
        ov = render_size(g, spec, pal, cut, words, body, total, tmp, os.path.join(outdir, f"v{key}.mp4"), mix)
        run("ffmpeg", "-v", "error", "-y", "-ss", f"{min(1.5, body / 2):.2f}", "-i", os.path.join(outdir, f"v{key}.mp4"), "-frames:v", "1", "-q:v", "3", os.path.join(outdir, f"cover{key}.jpg"))
        if key == "916": srt(words, ov.chs, os.path.join(outdir, "captions.srt"))
    run("rm", "-rf", tmp)
    print(json.dumps({"seconds": round(total, 1), "out": outdir, "layout": layout, "sizes": sizes, "words": len(words)}))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "transcribe": transcribe(a[1], a[2], a[a.index("--model") + 1] if "--model" in a else None)
    elif a[0] == "render": main(a[1], a[2])
    elif a[0] == "preview": main(a[1], a[2], True)
