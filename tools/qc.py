#!/usr/bin/env python3
"""Quality check before anything posts: video files, images and post copy.

usage:
  python3 tools/qc.py dir OUTDIR [--footage]        every v*.mp4 / cover*.jpg / gbp.png in a render folder -> OUTDIR/qc.json
  python3 tools/qc.py video FILE [--footage]        one video
  python3 tools/qc.py image FILE                    one image
  python3 tools/qc.py copy POSTS.json               [{"platform": "instagram", "text": "...", "firstComment": "..."}, ...]
  python3 tools/qc.py copy --platform x "text"      one caption
Prints {"ok", "errors": [...], "warnings": [...]} and exits 1 when there are errors.
Errors block posting. Warnings get a look (and a fix when they are real) but do not block.

Checks
  video  H.264 + yuv420p + AAC, 30 fps, the expected size for its name (v916 1080x1920, v169 1920x1080, v45 1080x1350,
         v11 1080x1080), length (9:16 at most 180 s so it stays a Reel/Short), file under 250 MB, loudness -18..-11 LUFS
         and true peak under -0.5 dB, no silence or black at the very start (the first second decides the scroll),
         and the 9:16 safe zones: text-like detail above y 220, below y 1540 (the centred footer logo is fine) or right
         of x 960 between y 900 and 1540 sits under the app's own buttons and captions. --footage relaxes the safe-zone
         check for real camera footage, where detail in those zones is the picture, not text.
  image  size, not blank, text touching the edge.
  copy   no emojis; "Piper Financial Group" never shortened; the podcast is "The Marketing Lens" (never "Lewis
         Marketing Lens"); a statistic needs a source link in the text or the first comment; platform length limits;
         hashtag counts (Instagram allows at most 5); no leftover placeholders like [NAME] or TODO.
"""
import json, os, re, subprocess, sys

SIZES = {"916": (1080, 1920), "169": (1920, 1080), "45": (1080, 1350), "11": (1080, 1080)}
LIMITS = {"x": 280, "twitter": 280, "bluesky": 300, "threads": 500, "instagram": 2200, "tiktok": 2200, "linkedin": 3000,
          "facebook": 5000, "gbp": 1500, "google": 1500, "youtube": 5000, "youtube_title": 100, "pinterest": 500}
EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF\U0000FE0F\U0000200D\U00002190-\U000021FF\U00003030\U000025A0-\U000025FF]")


def sh(*a):
    return subprocess.run(list(a), capture_output=True, text=True)


def size_key(path):
    m = re.match(r"v(916|169|45|11)", os.path.basename(path)) or re.match(r"cover(916|169|45|11)", os.path.basename(path))
    return m.group(1) if m else None


# ------------------------------------------------------------------ video
def frames_gray(path, times, W, H):
    import numpy as np
    out = []
    for t in times:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
        if len(r.stdout) == W * H: out.append((t, np.frombuffer(r.stdout, np.uint8).reshape(H, W)))
    return out


def text_density(g):
    """share of pixels on sharp, high-contrast edges (text and graphics score high, soft camera footage low)"""
    import numpy as np
    g = g.astype(np.int16)
    gx = np.abs(np.diff(g, axis=1))[:-1, :]; gy = np.abs(np.diff(g, axis=0))[:, :-1]
    return float(((gx > 70) | (gy > 70)).mean()) if g.size else 0.0


def safe_zones(path, dur, footage):
    import numpy as np
    warn = []; thr = 0.06 if footage else 0.025
    zones = {"top (under the app header)": (slice(0, 220), slice(0, 1080)),
             "bottom (under the caption and buttons)": (slice(1540, 1920), slice(0, 1080)),
             "right edge (under the like/comment buttons)": (slice(900, 1540), slice(960, 1080))}
    times = [t for t in np.linspace(0.6, max(0.7, dur - 0.4), 10)]
    hits = {}
    for t, g in frames_gray(path, times, 1080, 1920):
        for name, (ys, xs) in zones.items():
            z = g[ys, xs].copy()
            if name.startswith("bottom"): z[:, 300:780] = z[:, 300:780].mean()  # the centred footer logo is fine
            if text_density(z) > thr: hits.setdefault(name, []).append(round(float(t), 1))
    for name, ts in hits.items():
        if len(ts) >= 2: warn.append(f"safe zone: detail in the {name} at {ts[:5]} s; check nothing important sits there")
    return warn


def check_video(path, footage=False):
    E, W_ = [], []
    pr = sh("ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate:format=duration,size", "-of", "json", path)
    if pr.returncode: return {"ok": False, "errors": [f"{os.path.basename(path)}: cannot read the file"], "warnings": []}
    j = json.loads(pr.stdout); v = next((s for s in j["streams"] if s["codec_type"] == "video"), None); a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    dur = float(j["format"].get("duration", 0)); size = int(j["format"].get("size", 0)); n = os.path.basename(path)
    if not v: E.append(f"{n}: no video stream")
    else:
        if v["codec_name"] != "h264": E.append(f"{n}: video codec {v['codec_name']}, needs h264")
        if v.get("pix_fmt") != "yuv420p": E.append(f"{n}: pixel format {v.get('pix_fmt')}, needs yuv420p")
        num, den = (int(x) for x in v["r_frame_rate"].split("/")); fps = num / den if den else 0
        if not 23 <= fps <= 61: E.append(f"{n}: {fps:.1f} fps")
        k = size_key(path)
        if k and (v["width"], v["height"]) != SIZES[k]: E.append(f"{n}: {v['width']}x{v['height']}, expected {SIZES[k][0]}x{SIZES[k][1]}")
    if not a: E.append(f"{n}: no audio track (TikTok and Reels need one)")
    elif a["codec_name"] != "aac": W_.append(f"{n}: audio codec {a['codec_name']}")
    if dur < 3: E.append(f"{n}: only {dur:.1f} s long")
    if size_key(path) == "916" and dur > 180: E.append(f"{n}: {dur:.0f} s; 9:16 videos must be 180 s or less to post as a Reel/Short")
    if size > 250e6: E.append(f"{n}: {size / 1e6:.0f} MB, over 250 MB")
    if a:
        r = sh("ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-")
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr); p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
        if m:
            lufs = float(m[-1])
            if lufs < -20: E.append(f"{n}: too quiet ({lufs:.1f} LUFS, aim -15 to -13)")
            elif lufs > -11: E.append(f"{n}: too loud ({lufs:.1f} LUFS, aim -15 to -13)")
            elif not -16.5 <= lufs <= -12: W_.append(f"{n}: loudness {lufs:.1f} LUFS (aim -15 to -13)")
        if p and float(p[-1]) > -0.5: W_.append(f"{n}: true peak {float(p[-1]):.1f} dB, may clip")
        r = sh("ffmpeg", "-nostats", "-t", "3", "-i", path, "-af", "silencedetect=n=-45dB:d=0.6", "-f", "null", "-")
        if re.search(r"silence_start: (0|0\.0\d*|-[\d.]+)\b", r.stderr): W_.append(f"{n}: starts with more than 0.6 s of silence")
    r = sh("ffmpeg", "-nostats", "-t", "3", "-i", path, "-vf", "blackdetect=d=0.4:pix_th=0.08", "-an", "-f", "null", "-")
    if re.search(r"black_start:0(\.0+)?\b", r.stderr): E.append(f"{n}: opens on a black screen")
    if v and size_key(path) == "916" and (v["width"], v["height"]) == (1080, 1920): W_ += [f"{n}: {w}" for w in safe_zones(path, dur, footage)]
    return {"ok": not E, "errors": E, "warnings": W_}


# ------------------------------------------------------------------ image
def check_image(path):
    from PIL import Image
    import numpy as np
    E, W_ = [], []; n = os.path.basename(path)
    try: im = Image.open(path).convert("L")
    except Exception: return {"ok": False, "errors": [f"{n}: cannot open"], "warnings": []}
    k = size_key(path); g = np.asarray(im)
    if k and im.size != SIZES[k]: E.append(f"{n}: {im.size[0]}x{im.size[1]}, expected {SIZES[k][0]}x{SIZES[k][1]}")
    if n.startswith("gbp") and im.size[0] < 720: E.append(f"{n}: {im.size}, Google Business needs at least 720 px wide")
    if n.startswith("thumb") and im.size != (1280, 720): E.append(f"{n}: {im.size}, YouTube thumbnails are 1280x720")
    if os.path.getsize(path) > (2e6 if n.startswith("thumb") else 8e6): E.append(f"{n}: {os.path.getsize(path) / 1e6:.1f} MB, too big")
    if g.std() < 4: E.append(f"{n}: blank image")
    for side, strip in (("left", g[:, :6]), ("right", g[:, -6:]), ("top", g[:6, :]), ("bottom", g[-6:, :])):
        if text_density(strip) > 0.18: W_.append(f"{n}: sharp detail touching the {side} edge; check nothing is cut off")
    return {"ok": not E, "errors": E, "warnings": W_}


# ------------------------------------------------------------------ copy
def check_copy(text, platform="", first_comment=""):
    E, W_ = [], []; p = (platform or "").lower(); t = text or ""; both = t + "\n" + (first_comment or "")
    if EMOJI.search(both): E.append(f"{p or 'copy'}: contains an emoji ({''.join(sorted(set(EMOJI.findall(both))))})")
    if re.search(r"\bPiper\b(?! Financial Group)", both) or re.search(r"\bPFG\b", both): E.append(f"{p or 'copy'}: write \"Piper Financial Group\" in full")
    if re.search(r"Lewis Marketing Lens|Marketing Lens Podcast by Lewis", both, re.I): E.append(f"{p or 'copy'}: the podcast is \"The Marketing Lens\"")
    if re.search(r"\[(NAME|LINK|URL|TBD|X)\]|\bTODO\b|\bTBD\b|lorem ipsum|\{\{", both, re.I): E.append(f"{p or 'copy'}: leftover placeholder")
    stat = re.search(r"\b\d{1,3}(\.\d+)?\s?%|\b\d+ (in|out of) \d+\b|\b\d+x (more|faster|higher)", t)
    if stat and not re.search(r"https?://|\bsource:", both, re.I) and "lewismarketingoc.com" not in stat.string[max(0, stat.start() - 40):stat.end() + 40]:
        W_.append(f"{p or 'copy'}: statistic \"{stat.group(0)}\" with no source link in the post or first comment (fine only if it is our own number)")
    lim = LIMITS.get(p)
    if lim and len(t) > lim: E.append(f"{p}: {len(t)} characters, the limit is {lim}")
    tags = re.findall(r"(?<!\w)#\w+", t)
    if p == "instagram" and len(tags) > 5: E.append(f"instagram: {len(tags)} hashtags, the limit is 5")
    elif len(tags) > 5: W_.append(f"{p or 'copy'}: {len(tags)} hashtags (3 to 5 work best)")
    if p in ("x", "twitter", "bluesky", "threads") and len(tags) > 2: W_.append(f"{p}: {len(tags)} hashtags, 1 or 2 read better here")
    first = t.strip().split("\n")[0]
    if len(first) > 125 and p in ("instagram", "facebook", "linkedin"): W_.append(f"{p}: the first line (the hook) runs {len(first)} characters and gets cut off at 'more'")
    return {"ok": not E, "errors": E, "warnings": W_}


def merge(rs):
    return {"ok": all(r["ok"] for r in rs), "errors": [e for r in rs for e in r["errors"]], "warnings": [w for r in rs for w in r["warnings"]]}


def check_dir(d, footage=False):
    rs = []
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if re.match(r"v(916|169|45|11)(-\w+)?\.mp4$", f): rs.append(check_video(p, footage))
        elif re.match(r"(cover[\w-]*|gbp[\w-]*|thumb-[ab])\.(jpg|png)$", f): rs.append(check_image(p))
    res = merge(rs) if rs else {"ok": False, "errors": ["no videos or images found"], "warnings": []}
    json.dump(res, open(os.path.join(d, "qc.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    a = sys.argv[1:]; fo = "--footage" in a; a = [x for x in a if x != "--footage"]
    if a[0] == "dir": r = check_dir(a[1], fo)
    elif a[0] == "video": r = check_video(a[1], fo)
    elif a[0] == "image": r = check_image(a[1])
    elif a[0] == "copy":
        if a[1] == "--platform": r = check_copy(a[3], a[2])
        else: r = merge([check_copy(x.get("text", ""), x.get("platform", ""), x.get("firstComment", "")) for x in json.load(open(a[1]))])
    print(json.dumps(r, indent=1)); sys.exit(0 if r["ok"] else 1)
