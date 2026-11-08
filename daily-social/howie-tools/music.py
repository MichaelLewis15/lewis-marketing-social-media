"""Original energetic music bed: 126 BPM four-on-the-floor, synth bass, chord stabs, arp, hats, claps."""
import numpy as np, wave, sys

SR = 44100
BPM = 126
BEAT = 60 / BPM
BAR = BEAT * 4
rng = np.random.default_rng(7)

def env(n, a=0.002, d=0.2, s=0.0, total=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * (s + (1 - s) * np.exp(-t / d))
    return e

def note_hz(m):
    return 440 * 2 ** ((m - 69) / 12)

def kick(n=int(0.35 * SR)):
    t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * 1.0 + 0.15 * np.sin(ph * 2) * np.exp(-t * 40)

def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # crude highpass
    return x * np.exp(-np.arange(n) / SR * (18 if open_ else 70)) * 0.18

def clap():
    n = int(0.25 * SR)
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))
    t = np.arange(n) / SR
    e = np.exp(-t * 22)
    for off in (0.0, 0.011, 0.022):
        i = int(off * SR)
        e[i:] += 0.6 * np.exp(-(t[: n - i]) * 60)
    return x * e * 0.22

def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = 0
    for d in (-detune, 0, detune):
        out = out + 2 * ((t * f * (1 + d)) % 1) - 1
    return out / 3

def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    prev = 0.0
    for i in range(len(x)):
        prev = (1 - a) * x[i] + a * prev
        y[i] = prev
    return y

def place(buf, sig, t):
    i = int(t * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i]

VARIANTS = {
    0: dict(prog=[(57, [69, 72, 76]), (53, [65, 69, 72]), (60, [67, 72, 76]), (55, [67, 71, 74])], arp=[0, 1, 2, 3], seed=7),
    1: dict(prog=[(60, [72, 76, 79]), (55, [71, 74, 79]), (57, [72, 76, 81]), (53, [69, 72, 77])], arp=[0, 2, 1, 3], seed=11),
    2: dict(prog=[(50, [62, 65, 69]), (58, [62, 65, 70]), (53, [65, 69, 72]), (60, [64, 67, 72])], arp=[0, 1, 3, 2], seed=23),
    4: dict(prog=[(50, [62, 65, 69]), (58, [62, 65, 70]), (55, [62, 67, 70]), (57, [61, 64, 69])], arp=[0, 2, 3, 1], seed=31),
    3: dict(prog=[(52, [64, 67, 71]), (60, [64, 67, 72]), (55, [62, 67, 71]), (50, [62, 66, 69])], arp=[3, 2, 1, 0], seed=5),
}

def render(seconds, out, variant=0):
    V = VARIANTS[variant]
    global rng
    rng = np.random.default_rng(V["seed"])
    bars = int(np.ceil(seconds / BAR)) + 1
    N = int(bars * BAR * SR)
    drums = np.zeros(N); bass = np.zeros(N); synth = np.zeros(N)
    # progression: Am F C G (MIDI roots)
    prog = V["prog"]
    K = kick(); C = clap(); H = hat(); HO = hat(True)
    for b in range(bars):
        root, chord = prog[b % 4]
        t0 = b * BAR
        intro = b == 0
        for q in range(4):
            tb = t0 + q * BEAT
            if not intro or q >= 2:
                place(drums, K, tb)
            if q in (1, 3) and not intro:
                place(drums, C, tb)
            place(drums, HO if not intro else H, tb + BEAT / 2)
            for s in (0.25, 0.75):
                if not intro:
                    place(drums, H * 0.6, tb + s * BEAT)
        # offbeat bass (8ths, skipping downbeats)
        for e in range(8):
            if e % 2 == 1 or e == 6:
                n = int(BEAT / 2 * SR * 0.9)
                f = note_hz(root - 12 + (12 if e == 7 else 0))
                sig = saw(f, n, 0.004) * env(n, 0.003, 0.12, 0.3)
                place(bass, sig * (0.0 if intro else 0.5), t0 + e * BEAT / 2)
        # chord stabs on the "and" of 2 and 4 + 16th arp
        for pos in (1.5, 3.5, 2.75):
            n = int(0.22 * SR)
            sig = sum(saw(note_hz(m), n, 0.006) for m in chord) / 3
            place(synth, sig * env(n, 0.002, 0.08) * 0.45, t0 + pos * BEAT)
        arp = chord + [chord[0] + 12]
        for s in range(16):
            n = int(BEAT / 4 * SR * 0.8)
            m = arp[V["arp"][s % 4]] + 12
            sig = np.sign(np.sin(2 * np.pi * note_hz(m) * np.arange(n) / SR)) * env(n, 0.001, 0.05)
            place(synth, sig * 0.08 * (0.6 if intro else 1), t0 + s * BEAT / 4)
    bass = lowpass(bass, 700)
    synth = lowpass(synth, 4200)
    # sidechain pump from kick positions
    pump = np.ones(N)
    for b in range(bars):
        for q in range(4):
            i = int((b * BAR + q * BEAT) * SR)
            n = int(BEAT * SR)
            t = np.arange(min(n, N - i)) / SR
            pump[i:i + len(t)] = np.minimum(pump[i:i + len(t)], 0.35 + 0.65 * (1 - np.exp(-t * 14)))
    mix = drums * 0.9 + (bass + synth) * pump
    # crash/riser at bar 1 end (into drop)
    n = int(BAR * SR)
    riser = rng.standard_normal(n) * np.linspace(0, 1, n) ** 2 * 0.12
    place(mix, riser, 0)
    mix = mix[: int(seconds * SR)]
    fade = int(1.2 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.1)
    mix = mix / np.max(np.abs(mix)) * 0.89
    stereo = np.stack([mix, np.roll(mix, 30)], axis=1)
    data = (stereo * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())

if __name__ == "__main__":
    render(float(sys.argv[1]), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
