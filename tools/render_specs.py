#!/usr/bin/env python3
"""Render every given video spec that has an "out" folder (used by .github/workflows/render-videos.yml).

usage: python3 tools/render_specs.py spec.json [spec.json ...]
A spec is rendered when it has "out" (repo-relative output folder, e.g. "daily/video/2026-11-20-am").
Writes tools/render/results/<spec name>.json {spec, out, ok, seconds, files, voiceCheck, error, sha}.
"""
import json, os, sys, subprocess, hashlib, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "tools" / "render" / "results"; RES.mkdir(parents=True, exist_ok=True)
bad = 0
for sp in sys.argv[1:]:
    p = ROOT / sp
    if not p.is_file(): continue
    spec = json.loads(p.read_text())
    if not spec.get("out"): print(f"skip {sp}: no out"); continue
    out = ROOT / spec["out"]; out.mkdir(parents=True, exist_ok=True)
    tool = ["daily-social/clips/clip.py", "render"] if spec.get("source") else ["daily-social/hl-weekly/render_weekly.py"]
    r = subprocess.run([sys.executable, str(ROOT / tool[0]), *tool[1:], str(p), str(out)], capture_output=True, text=True)
    res = {"spec": sp, "out": spec["out"], "ok": r.returncode == 0, "at": datetime.datetime.utcnow().isoformat() + "Z"}
    if r.returncode == 0:
        info = json.loads(r.stdout.strip().splitlines()[-1]); res.update(seconds=info["seconds"])
        res["files"] = {f.name: hashlib.sha1(f.read_bytes()).hexdigest()[:10] for f in sorted(out.iterdir()) if f.is_file()}
        vcs = sorted(out.glob("voice-check*.json"))
        if vcs:
            checks = [c for vc in vcs for c in json.loads(vc.read_text()) if c]
            res["voiceCheck"] = {"ok": all(c["ok"] for c in checks), "flagged": [c for c in checks if not c["ok"]]}
    else:
        res["error"] = (r.stderr or r.stdout)[-1500:]; bad += 1
    (RES / (p.stem + ".json")).write_text(json.dumps(res, indent=1))
    print(json.dumps(res)[:600])
sys.exit(1 if bad else 0)
