"""Add an animated Howie (hop in, hello bubble, idle/point, cheer) to an existing 1080x1920 reel, with whoosh + pop sounds."""
import sys, os, json, subprocess, wave, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))

def timeline(d, x=200, y=1590, s=1.25, hello=True):
    MV = [dict(t=0, x=-200, y=y, s=s), dict(t=0.2, x=x, y=y, s=s, d=0.6, h=150)]
    PO = [dict(t=0, p="idle")]; BU = []
    if hello and d > 6:
        PO.append(dict(t=0.9, p="wave")); PO.append(dict(t=2.6, p="idle"))
        BU.append(dict(t=0.95, d=1.6, text="Hi, I'm Howie!", x=x + 135, y=y - 300, side="l"))
    t = 3.4; k = 0
    while t < d - 3.2:
        PO.append(dict(t=t, p="pointR", a=100)); PO.append(dict(t=t + 1.6, p="idle"))
        if k % 2 == 1: MV.append(dict(t=t + 2.0, x=x + (25 if k % 4 == 1 else 0), y=y, s=s, d=0.4, h=45))
        t += 3.2; k += 1
    PO.append(dict(t=max(1.0, d - 2.4), p="cheer"))
    return dict(MV=MV, PO=PO, BU=BU)

def sfx(wav_in, wav_out, T):
    with wave.open(wav_in) as w: sr = w.getframerate(); ch = w.getnchannels(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, ch).astype(np.float32) / 32767
    if ch == 1: x = np.repeat(x, 2, axis=1)
    rng = np.random.default_rng(5); prev = None
    for m in T["MV"]:
        if m.get("d"):
            n = int((m["d"] + .15) * sr); noise = rng.standard_normal(n); tt = np.arange(n) / sr
            env = np.sin(np.pi * np.clip(tt / (m["d"] + .15), 0, 1)) ** 2
            # cheap swept low-pass via moving average of varying width
            y = np.convolve(noise, np.ones(24) / 24, mode="same") * (0.6 + 0.4 * env)
            y = y / (np.abs(y).max() + 1e-9) * env * (0.28 if m["h"] > 100 else 0.14)
            pan = 1 if prev is None or m["x"] >= prev else -1
            i0 = int(m["t"] * sr); j = min(len(x), i0 + n)
            if i0 < len(x): x[i0:j, 0] += y[: j - i0] * (0.6 - 0.3 * pan); x[i0:j, 1] += y[: j - i0] * (0.6 + 0.3 * pan)
        prev = m["x"]
    for b in T["BU"]:
        n = int(.12 * sr); tt = np.arange(n) / sr; pop = np.sin(2 * np.pi * (900 - 2500 * tt) * tt) * np.exp(-tt * 45) * 0.3
        i0 = int(b["t"] * sr); j = min(len(x), i0 + n); x[i0:j, :] += pop[: j - i0, None]
    x = np.tanh(x * 1.02); x = x / max(1e-9, np.abs(x).max()) * 0.89
    with wave.open(wav_out, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype(np.int16).tobytes())

def run(src, dst, page="reel-generic.html", **kw):
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    T = timeline(d, **kw); tmp = tempfile.mkdtemp(dir="/tmp/claude-0")
    json.dump(T, open(f"{tmp}/tl.json", "w"))
    subprocess.run(["node", os.path.join(HERE, "howie", "render_any.js"), os.path.join(HERE, "howie", page), f"{tmp}/tl.json", str(d), f"{tmp}/fr"], check=True, env=dict(os.environ, NODE_PATH=subprocess.check_output(["npm", "root", "-g"]).decode().strip()))
    has_audio = bool(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", src]).strip())
    if has_audio:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "2", "-ar", "44100", f"{tmp}/a.wav"], check=True)
        sfx(f"{tmp}/a.wav", f"{tmp}/b.wav", T)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-framerate", "30", "-i", f"{tmp}/fr/h%04d.png"]
    if has_audio: cmd += ["-i", f"{tmp}/b.wav"]
    cmd += ["-filter_complex", "[0:v][1:v]overlay=0:1000:eof_action=pass[v]", "-map", "[v]"]
    if has_audio: cmd += ["-map", "2:a", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-shortest", dst]
    subprocess.run(cmd, check=True)
    subprocess.run(["rm", "-rf", tmp])
    return T

if __name__ == "__main__":
    a = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    run(sys.argv[1], sys.argv[2], **a); print(sys.argv[2])
