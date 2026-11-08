#!/usr/bin/env python3
"""Drip712 reel builder: 1080x1920 (9:16) scenes rendered with Chromium, joined with ffmpeg
(slow push-in per scene, crossfades) over an original synthesized music bed.

Usage: python3 reel_drip.py reels.json OUT_DIR
reels.json: [{"name": "03-first-visit", "scenes": [
   {"kind": "hook", "eyebrow": "First time?", "headline": "Your first drip, <em>step by step</em>"},
   {"kind": "step", "n": "1", "text": "Book, or call or text", "detail": "Not sure which drip? Say so."},
   {"kind": "end", "headline": "Book at <em>drip712.com</em>", "sub": "Or call or text 712-403-2036"}], "sec": 3.2, "key": "D"}]
Writes OUT_DIR/<name>.mp4 and OUT_DIR/posters/<name>.jpg.
"""
import json, os, sys, asyncio, subprocess, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art  # noqa
from render_drip import CSS, rich, esc  # noqa

RCSS = CSS + """
.reel{position:relative;width:1080px;height:1920px;overflow:hidden;background:#fbf8f4;font-family:DM}
.reel.navy{background:#143a4f}
.rb{position:absolute;border-radius:50%}
.mid{position:absolute;left:96px;right:96px;top:0;bottom:300px;display:flex;flex-direction:column;justify-content:center}
.reel .eyebrow{font-size:30px}
.reel h1{font-size:118px;line-height:1.04}
.reel.navy h1{color:#fff}
.reel .sub{font-size:44px;line-height:1.35;margin-top:34px}
.reel.navy .sub{color:#c9dde2}
.num{width:150px;height:150px;border-radius:50%;background:#2fa3b2;color:#fff;display:grid;place-items:center;font:500 84px Fraunces;margin-bottom:46px}
.stxt{font:500 92px/1.1 Fraunces;color:#143a4f;letter-spacing:-.015em}
.sdet{font:400 46px/1.35 DM;color:#55656e;margin-top:30px}
.rart{position:absolute;left:0;right:0;bottom:330px;display:flex;justify-content:center}
.rfoot{position:absolute;left:0;right:0;bottom:0;height:250px;background:#143a4f;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px}
.rfoot::before{content:"";position:absolute;left:0;right:0;top:-36px;height:38px;background:#143a4f;clip-path:path('M0 38 C 260 0 760 0 1080 30 V38Z')}
.rfoot .word{font-size:72px}.rfoot .word small{font-size:20px;text-align:center}
.reel.navy .rfoot::before{background:#0f2f40}.reel.navy .rfoot{background:#0f2f40}
.dots{position:absolute;top:120px;left:96px;display:flex;gap:12px}.dots i{width:46px;height:8px;border-radius:4px;background:#143a4f22}.dots i.on{background:#2fa3b2}
"""


def scene_html(sc, idx, total):
    k = sc.get("kind", "hook")
    navy = sc.get("navy") or k == "end"
    blobs = ('<div class="rb" style="left:640px;top:-220px;width:700px;height:700px;background:%s;opacity:%s"></div>'
             '<div class="rb" style="left:-260px;top:1080px;width:560px;height:560px;background:%s;opacity:%s"></div>') % (
        ("#2fa3b2", ".18", "#2fa3b2", ".10") if navy else ("#dff1f2", ".85", "#f2d9cf", ".6"))
    dots = "" if k in ("hook", "end") else '<div class="dots">' + "".join(f'<i class="{"on" if i <= idx else ""}"></i>' for i in range(1, total - 1)) + '</div>'
    a = art.ARTS.get(sc.get("art") or "")
    arth = f'<div class="rart">{a(470)}</div>' if a else ""
    if k == "step":
        mid = (f'<div class="mid" style="bottom:{760 if a else 300}px"><div class="num">{esc(sc.get("n", ""))}</div><div class="stxt">{rich(sc.get("text", ""))}</div>'
               + (f'<div class="sdet">{rich(sc["detail"])}</div>' if sc.get("detail") else "") + '</div>')
    else:
        mid = (f'<div class="mid" style="bottom:{760 if a else 300}px">' + (f'<div class="eyebrow">{esc(sc["eyebrow"])}</div>' if sc.get("eyebrow") else "")
               + f'<h1>{rich(sc.get("headline", ""))}</h1>' + (f'<p class="sub">{rich(sc["sub"])}</p>' if sc.get("sub") else "") + '</div>')
    foot = ('<div class="rfoot"><div class="mark"><div class="drop"></div><div class="word">drip <span>712</span>'
            '<small>Wellness from within</small></div></div></div>')
    return (f"<!doctype html><html><head><meta charset=utf-8><style>{RCSS}</style></head><body>"
            f"<div class='reel{' navy' if navy else ''}'>{blobs}{dots}{mid}{arth}{foot}</div></body></html>")


def music(path, dur, key="D", seed=1):
    sr = 44100
    t = np.arange(int(sr * dur)) / sr
    base = {"C": 261.63, "D": 293.66, "E": 329.63, "F": 349.23, "G": 392.0, "A": 220.0}[key]
    prog = [[0, 4, 7, 11], [9, 12, 16, 19], [5, 9, 12, 16], [7, 11, 14, 17]]  # Imaj7 vi IV V(add)
    bar = 2.4
    out = np.zeros_like(t)
    rng = np.random.default_rng(seed)
    for i in range(int(dur / bar) + 1):
        ch = prog[i % 4]
        s, e = int(i * bar * sr), int(min(dur, (i + 1) * bar + 0.6) * sr)
        if s >= len(t):
            break
        tt = t[s:e] - t[s]
        env = np.minimum(1, tt / 0.5) * np.exp(-tt / 3.2)
        for semi in ch:
            f = base / 2 * 2 ** (semi / 12)
            out[s:e] += 0.07 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt + .3))
        # soft plucked arpeggio
        for j in range(4):
            ps = s + int(j * bar / 4 * sr)
            if ps >= len(t):
                break
            pe = min(len(t), ps + int(1.2 * sr))
            pt = t[ps:pe] - t[ps]
            f = base * 2 ** (ch[(j + i) % 4] / 12)
            out[ps:pe] += 0.05 * np.exp(-pt * 3.5) * np.sin(2 * np.pi * f * pt) * (0.8 + 0.2 * rng.random())
    fade = np.minimum(1, np.minimum(t / 1.0, (dur - t) / 1.5))
    out = out * fade
    out = out / (np.abs(out).max() + 1e-9) * 0.5
    st = np.stack([out, np.roll(out, 300)], 1)
    with wave.open(path, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((st * 32767).astype("<i2").tobytes())


async def shots(reel, tmp):
    from playwright.async_api import async_playwright
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    files = []
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        n = len(reel["scenes"])
        for i, sc in enumerate(reel["scenes"]):
            h = os.path.join(tmp, f"s{i}.html"); open(h, "w").write(scene_html(sc, i, n))
            await pg.goto("file://" + h, wait_until="load")
            await pg.evaluate("document.fonts.ready")
            f = os.path.join(tmp, f"s{i}.png"); await pg.screenshot(path=f); files.append(f)
        await b.close()
    return files


def build(reel, out):
    name = reel["name"]
    tmp = os.path.join("/tmp", "reel-" + name); os.makedirs(tmp, exist_ok=True)
    os.makedirs(os.path.join(out, "posters"), exist_ok=True)
    files = asyncio.run(shots(reel, tmp))
    sec = reel.get("sec", 3.2); xf = 0.5; fps = 30
    durs = [sc.get("sec", sec) for sc in reel["scenes"]]
    total = sum(durs) - xf * (len(durs) - 1)
    wav = os.path.join(tmp, "m.wav"); music(wav, total + 0.2, reel.get("key", "D"), seed=len(name))
    inp, flt = [], []
    for i, (f, d) in enumerate(zip(files, durs)):
        inp += ["-loop", "1", "-t", f"{d}", "-i", f]
        fr = int(d * fps)
        flt.append(f"[{i}:v]scale=1188:2112,zoompan=z='min(1+0.06*on/{fr},1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={fps},setsar=1,format=yuv420p[v{i}]")
    last, off = "v0", 0.0
    for i in range(1, len(files)):
        off += durs[i - 1] - xf
        flt.append(f"[{last}][v{i}]xfade=transition=fade:duration={xf}:offset={off:.2f}[x{i}]")
        last = f"x{i}"
    inp += ["-i", wav]
    mp4 = os.path.join(out, f"{name}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inp, "-filter_complex", ";".join(flt), "-map", f"[{last}]", "-map", f"{len(files)}:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", files[0], "-vf", "scale=540:960", "-q:v", "4", os.path.join(out, "posters", f"{name}.jpg")], check=True)
    return {"name": name, "file": mp4, "seconds": round(total, 1)}


if __name__ == "__main__":
    reels = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    for r in reels:
        print(json.dumps(build(r, out)))
