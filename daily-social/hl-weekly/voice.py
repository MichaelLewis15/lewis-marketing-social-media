"""Voiceover for the Lewis Marketing video engine.

Kokoro v1.0 speaks each scene's line; faster-whisper tiny.en listens back to it, which gives word timings for the
burned-in captions and a pronunciation check (voice-check.json in the output folder).

Michael's rule (Nov 21, 2026): every Lewis Marketing voiceover is the male voice "lm_male" (Kokoro am_fenrir 80% +
am_puck 20%, full-precision model) read the expressive way:
- each line is spoken one unit at a time (sentences, plus setups ending in ":" or a dash);
- Praat reshapes the pitch: a wider melody, a lift at each new sentence, questions rise, statements settle,
  and *starred* words in a "vo" line are stressed (pitch lift and held a touch longer; the stars never show on screen).
  With no stars, numbers get the stress. Star the one or two words a person would naturally stress;
- pauses are a beat or two by what was just said: longest after a question (~0.6 s), a setup ending in ":" or a
  punchy line of 5 words or fewer (~0.5 s), a breath before the closing line (~0.55 s), ~0.35 s otherwise.
"af_heart" (the old female voice) still works with "voiceName": "af_heart" and "expressive": false.

Models live on the repo's "models" branch (the render containers cannot reach Hugging Face):
  git clone --depth 1 -b models <repo url> daily-social/models
  pip install kokoro-onnx soundfile faster-whisper   (--break-system-packages in the container)

Pronunciation: LEXICON rewrites brand names, acronyms, web addresses and abbreviations into words the voice
says correctly. Add to it whenever voice-check.json flags a word (and keep the on-screen text unchanged).
"""
import os, re, difflib, wave
import numpy as np

MODELS = os.environ.get("LM_MODELS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models"))

MONTHS = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "Jun": "June", "Jul": "July", "Aug": "August",
          "Sep": "September", "Sept": "September", "Oct": "October", "Nov": "November", "Dec": "December"}
LEXICON = [  # (regex, spoken form) applied in order, case-sensitive
    (r"https?://", ""),
    (r"\blewismarketingoc\.com\b", "Lewis Marketing O.C. dot com"),
    (r"@lewismarketingoc\b", "at Lewis Marketing O.C."),
    (r"\bchatgpt\.com/business-hub\b", "chat G.P.T. dot com slash business hub"),
    (r"\b([A-Za-z0-9-]+)\.(com|org|net|io|ai)/([\w/-]+)", lambda m: f"{m.group(1)} dot {m.group(2)} slash " + m.group(3).replace("-", " ").replace("/", " slash ")),
    (r"\b([A-Za-z0-9-]+)\.(com|org|net|io)\b", r"\1 dot \2"),
    (r"\bGoHighLevel\b", "Go High Level"), (r"\bHighLevel\b", "High Level"), (r"\bLeadConnector\b", "Lead Connector"),
    (r"\bChatGPT\b", "Chat G.P.T."), (r"\bOpenAI\b", "Open A.I."), (r"\bGPT\b", "G.P.T."), (r"\bAI\b", "A.I."),
    (r"\bSEO\b", "S.E.O."), (r"\bCRM\b", "C.R.M."), (r"\bGBP\b", "Google Business Profile"), (r"\bSMS\b", "S.M.S."),
    (r"\bAPI\b", "A.P.I."), (r"\bROI\b", "R.O.I."), (r"\bPPC\b", "P.P.C."), (r"\bDNS\b", "D.N.S."), (r"\bFAQs?\b", "F.A.Q.s"),
    (r"\bURL\b", "U.R.L."), (r"\bCTA\b", "call to action"), (r"\bB2B\b", "B to B"), (r"\bKPI(s?)\b", r"K.P.I.\1"),
    (r"\bU\.S\.", "U.S."), (r"\bNW\b", "Northwest"), (r"\bIA\b", "Iowa"), (r"\bOC\b", "O.C."),
    (r"\bSioux\b", "Soo"), (r"\bLe Mars\b", "Luh Marz"), (r"\bDrip712\b", "Drip seven twelve"),
    (r"\bvs\.?", "versus"), (r"&", " and "), (r"\be-commerce\b", "ecommerce"),
    (r"(\d)\s*-\s*(\d)", r"\1 to \2"),
    (r"(\d+(?:\.\d+)?)%", r"\1 percent"), (r"\$(\d[\d,]*(?:\.\d+)?)([KkMm])\b", lambda m: m.group(1) + (" thousand" if m.group(2) in "Kk" else " million") + " dollars"),
    (r"\b(" + "|".join(MONTHS) + r")\.?(?=\s+\d)", lambda m: MONTHS[m.group(1)]),
    (r"\s*/\s*", " slash "), (r"\.\.+", "."), (r"\s+", " "),
]


def speakable(text):
    t = str(text)
    for pat, rep in LEXICON: t = re.sub(pat, rep, t)
    return t.strip()


_K = _W = None


def _models():
    global _K, _W
    if _K is None:
        from kokoro_onnx import Kokoro
        from faster_whisper import WhisperModel
        mp = os.path.join(MODELS, "kokoro-v1.0.onnx")  # full precision (downloaded by the render Action)
        if not os.path.exists(mp): mp = os.path.join(MODELS, "kokoro-v1.0.int8.onnx")
        if not os.path.exists(mp): raise SystemExit("voice models missing: git clone --depth 1 -b models <repo url> daily-social/models")
        _K = Kokoro(mp, os.path.join(MODELS, "voices-v1.0.bin"))
        _W = WhisperModel(os.path.join(MODELS, "whisper-tiny.en"), device="cpu", compute_type="int8")
    return _K, _W


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower().replace(".", "")).split()


DEFAULT_VOICE = "lm_male"


def _voice(k, name):
    if name in (None, "", "lm_male"):
        return k.get_voice_style("am_fenrir") * 0.8 + k.get_voice_style("am_puck") * 0.2
    return name


def units(text):
    """spoken units: sentences, plus setups ending in a colon or a dash"""
    return [p for p in re.split(r"(?<=[.!?:])\s+|\s+(?:--|\u2014)\s+", str(text).strip()) if p]


def _speed(u, base):
    n = len(u.replace("*", "").split())
    if u.endswith("?"): return base * 0.96
    if u.endswith(":"): return base * 0.98
    if n <= 5: return base * 0.93   # punchy line: land it
    return base * 1.03


def _pause(u, closing_next, rng):
    """a beat or two, by what was just said (seconds)"""
    n = len(u.replace("*", "").split())
    if u.endswith("?"): b = 0.62      # let the question hang
    elif u.endswith(":"): b = 0.48    # setup -> payoff
    elif u.endswith("!"): b = 0.45
    elif n <= 5: b = 0.52             # punchy line lands
    else: b = 0.34
    if closing_next: b = max(b, 0.55)  # breath before the closing line
    return b * rng.uniform(0.92, 1.08)


def _key(wd):
    return re.sub(r"[^a-z0-9]", "", wd.lower())


def _shape(a, sr, unit, stress, w, range_k=1.25):
    """Praat pitch reshaping: wider melody, sentence-start lift, question rise / statement settle, stressed words"""
    try:
        import parselmouth
        from parselmouth.praat import call
    except ImportError:
        return a
    dur = len(a) / sr
    snd = parselmouth.Sound(a.astype(np.float64), sr)
    man = call(snd, "To Manipulation", 0.01, 60, 300); tier = call(man, "Extract pitch tier")
    npts = call(tier, "Get number of points")
    if not npts: return a
    t = np.array([call(tier, "Get time from index", i) for i in range(1, npts + 1)])
    f = np.array([call(tier, "Get value at index", i) for i in range(1, npts + 1)]); med = np.median(f)
    spans = []
    if stress:
        a16 = np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)
        segs, _ = w.transcribe(a16, word_timestamps=True, language="en")
        spans = [(x.start, x.end) for sg in segs for x in sg.words if _key(x.word) in stress]
    q, ex = unit.endswith("?"), unit.endswith("!")
    g = med * (f / med) ** range_k
    g = g * np.where(t / dur < 0.2, 1.06, 1.0)
    for a0, a1 in spans:
        mid, wid = (a0 + a1) / 2, max(0.06, (a1 - a0) / 2)
        g = g * np.where((t >= a0 - 0.04) & (t <= a1 + 0.02), 1 + 0.16 * np.exp(-((t - mid) / wid) ** 2), 1.0)
    if q: g = g * np.where(t > dur - 0.45, 1 + 0.22 * (t - (dur - 0.45)) / 0.45, 1.0)
    else: g = g * np.where(t > dur - 0.5, 1 - (0.04 if ex else 0.08) * (t - (dur - 0.5)) / 0.5, 1.0)
    call(tier, "Remove points between", 0, dur)
    for ti, gi in zip(t, g): call(tier, "Add point", float(ti), float(gi))
    call([man, tier], "Replace pitch tier")
    if spans:
        dt = call(man, "Extract duration tier")
        for a0, a1 in spans:
            for tt, v in ((max(0, a0 - 0.01), 1.0), (a0 + 0.01, 1.1), (a1 - 0.01, 1.1), (a1 + 0.01, 1.0)): call(dt, "Add point", tt, v)
        call([man, dt], "Replace duration tier")
    return np.asarray(call(man, "Get resynthesis (overlap-add)").values[0], np.float32)


def _say(k, w, line, voice, speed, expressive, seed):
    """one scene line -> samples. expressive: unit by unit, reshaped pitch, natural pauses"""
    sty = _voice(k, voice); sr = 24000
    def gen(text, sp):
        s, r = k.create(text, voice=sty, speed=sp, lang="en-us")
        s = np.asarray(s, np.float32); nz = np.where(np.abs(s) > 0.01)[0]
        return (s[max(0, nz[0] - int(0.03 * r)): nz[-1] + int(0.1 * r)] if len(nz) else s), r
    if not expressive:
        return gen(speakable(line.replace("*", "")), speed)
    rng = np.random.default_rng(seed); us = units(line); parts = []
    for i, u in enumerate(us):
        stars = re.findall(r"\*([^*]+)\*", u)
        plain = u.replace("*", "")
        stress = {_key(x) for st in stars for x in re.split(r"[\s-]+", speakable(st)) if _key(x)}
        if not stars: stress = {_key(x) for x in plain.split() if re.search(r"\d", x)}
        a, sr = gen(speakable(plain), _speed(u, speed))
        a = _shape(a, sr, plain, stress, w)
        parts.append(a)
        if i < len(us) - 1: parts.append(np.zeros(int(sr * _pause(u, i == len(us) - 2 and len(us) > 2, rng)), np.float32))
    return np.concatenate(parts), sr


def narrate(lines, tmp, voice=DEFAULT_VOICE, speed=1.0, expressive=True):
    """lines: one string (or None) per scene. returns per scene None or {wav, dur, words[(text, start, end)], check}"""
    k, w = _models(); out = []
    if voice in (None, ""): voice = DEFAULT_VOICE
    expressive = bool(expressive) and voice != "af_heart"
    for n, raw in enumerate(lines):
        if not raw or not str(raw).strip(): out.append(None); continue
        line = str(raw).replace("*", "")
        spoken = speakable(line)
        samples, sr = _say(k, w, str(raw), voice, speed * (1.04 if voice == DEFAULT_VOICE else 1.0), expressive, n + 7)
        path = os.path.join(tmp, f"vo{n}.wav")
        with wave.open(path, "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
        a16 = np.interp(np.arange(0, len(samples), sr / 16000), np.arange(len(samples)), samples).astype(np.float32)
        segs, _ = w.transcribe(a16, word_timestamps=True, beam_size=5, language="en")
        heard = [(x.word.strip(), x.start, x.end) for s in segs for x in s.words]
        words = align(str(line), spoken, heard, len(samples) / sr)
        exp, got = _norm(spoken), _norm(" ".join(h[0] for h in heard))
        # compare letters only, so "lewismarketingoc" vs "lewis marketing oc" or "e commerce" vs "ecommerce" still match
        ratio = difflib.SequenceMatcher(None, "".join(exp), "".join(got)).ratio()
        diff = [f"{' '.join(exp[a1:a2])} -> {' '.join(got[b1:b2])}" for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, exp, got).get_opcodes() if op != "equal"]
        out.append(dict(wav=path, dur=len(samples) / sr, words=words,
                        check=dict(scene=n, text=line, spoken=spoken, heard=" ".join(h[0] for h in heard), match=round(ratio, 3), ok=ratio >= 0.9 or _numbers_only(diff), diffs=diff[:12])))
    return out


NUMWORDS = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
                "eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million percent dollars".split())


def _numbers_only(diffs):
    """the only differences are numbers written as digits ("four fifty five -> 4 55"), which is how whisper writes them"""
    if not diffs: return True
    for d in diffs:
        a, _, b = d.partition(" -> ")
        if not (set(a.split()) <= NUMWORDS | {"and", "a"} and re.fullmatch(r"[\d\s.,:%$]*", b)): return False
    return True


def align(original, spoken, heard, dur):
    """map the on-screen words onto the heard word timings (proportional where the counts differ)"""
    orig = original.split()
    if not heard: return [(wd, dur * i / len(orig), dur * (i + 1) / len(orig)) for i, wd in enumerate(orig)]
    if len(heard) == len(orig): return [(o, h[1], h[2]) for o, h in zip(orig, heard)]
    # spread each original word over its share of the spoken characters, inside the heard span
    t0, t1 = heard[0][1], heard[-1][2]; lens = [max(1, len(speakable(o))) for o in orig]; tot = sum(lens); acc = 0; res = []
    for o, l in zip(orig, lens):
        a = t0 + (t1 - t0) * acc / tot; acc += l; b = t0 + (t1 - t0) * acc / tot
        res.append((o, a, b))
    return res
