"""Voiceover for the Lewis Marketing video engine.

Kokoro v1.0 (int8 ONNX) speaks each scene's line; faster-whisper tiny.en listens back to it, which gives
word timings for the burned-in captions and a pronunciation check (voice-check.json in the output folder).

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
        mp = os.path.join(MODELS, "kokoro-v1.0.int8.onnx")
        if not os.path.exists(mp): raise SystemExit("voice models missing: git clone --depth 1 -b models <repo url> daily-social/models")
        _K = Kokoro(mp, os.path.join(MODELS, "voices-v1.0.bin"))
        _W = WhisperModel(os.path.join(MODELS, "whisper-tiny.en"), device="cpu", compute_type="int8")
    return _K, _W


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower().replace(".", "")).split()


def narrate(lines, tmp, voice="af_heart", speed=1.0):
    """lines: one string (or None) per scene. returns per scene None or {wav, dur, words[(text, start, end)], check}"""
    k, w = _models(); out = []
    for n, line in enumerate(lines):
        if not line or not str(line).strip(): out.append(None); continue
        spoken = speakable(line)
        samples, sr = k.create(spoken, voice=voice, speed=speed, lang="en-us")
        samples = np.asarray(samples, np.float32)
        nz = np.where(np.abs(samples) > 0.01)[0]  # trim silence at both ends
        if len(nz): samples = samples[max(0, nz[0] - int(0.03 * sr)): nz[-1] + int(0.12 * sr)]
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
                        check=dict(scene=n, text=line, spoken=spoken, heard=" ".join(h[0] for h in heard), match=round(ratio, 3), ok=ratio >= 0.9, diffs=diff[:12])))
    return out


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
