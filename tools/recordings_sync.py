#!/usr/bin/env python3
"""Finds new footage in Lewis Marketing's HighLevel Media Storage folder "Video recordings", transcribes it
and records it in daily-social/clips/sources.json for the video-clips scheduled task.

kind: "talking" (portrait and under 5 minutes: Michael's phone videos to polish) or "long" (everything else:
recordings to cut into clips). Lewis Marketing location only. Needs HL_TOKEN.
"""
import json, os, sys, re, time, datetime, pathlib, subprocess, urllib.request
import requests

LOC = "Auzaxxusb4MezZd78QIC"; API = "https://services.leadconnectorhq.com"; CDN = "https://assets.cdn.filesafe.space/"
FOLDER_NAME = "Video recordings"
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "daily-social" / "clips" / "sources.json"; TR = ROOT / "daily-social" / "clips" / "transcripts"
tok = os.environ.get("HL_TOKEN")
if not tok: print("::warning::HL_TOKEN missing"); sys.exit(0)
H = {"Authorization": f"Bearer {tok}", "Version": "2021-07-28", "Accept": "application/json"}


def get(path, **params):
    for a in range(4):
        r = requests.get(API + path, headers=H, params=params, timeout=120)
        if r.status_code == 429 or r.status_code >= 500: time.sleep(5 * (a + 1)); continue
        r.raise_for_status(); return r.json()
    r.raise_for_status()


def folder_id():
    if os.environ.get("HL_RECORDINGS_FOLDER", "6af8ca80893246071f817d87"): return os.environ.get("HL_RECORDINGS_FOLDER", "6af8ca80893246071f817d87")
    d = get("/medias/files", altId=LOC, altType="location", type="folder", limit=100, offset=0, query=FOLDER_NAME)
    for f in d.get("files") or []:
        if (f.get("name") or "").strip().lower() == FOLDER_NAME.lower(): return f["_id"]
    return None


def slug(name):
    base = re.sub(r"\.[A-Za-z0-9]+$", "", name)
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:60] or "recording"


def main():
    fid = folder_id()
    if not fid: print(f'No "{FOLDER_NAME}" folder in Media Storage yet.'); return
    srcs = json.loads(SRC.read_text()) if SRC.exists() else {}
    known = {v["fileId"] for v in srcs.values()}
    d = get("/medias/files", altId=LOC, altType="location", type="file", parentId=fid, limit=100, offset=0, sortBy="createdAt", sortOrder="desc")
    TR.mkdir(parents=True, exist_ok=True); new = 0
    for f in d.get("files") or []:
        if f["_id"] in known: continue
        name = f.get("name") or f["_id"]
        if not re.search(r"\.(mp4|mov|m4v|webm|mkv)$", name, re.I) and "video" not in (f.get("contentType") or f.get("type") or ""): continue
        url = CDN + f["path"] if f.get("path") else f.get("url")
        s = slug(name); k = s; n = 2
        while k in srcs: k = f"{s}-{n}"; n += 1
        out = TR / f"{k}.json"
        r = subprocess.run([sys.executable, str(ROOT / "daily-social/clips/clip.py"), "transcribe", url, str(out)], capture_output=True, text=True)
        if r.returncode:
            print(f"::warning::transcribe failed for {name}: {r.stderr[-500:]}"); continue
        tr = json.loads(out.read_text())
        kind = "talking" if tr["height"] > tr["width"] and tr["duration"] < 300 else "long"
        srcs[k] = {"fileId": f["_id"], "name": name, "url": url, "duration": round(tr["duration"], 1), "width": tr["width"], "height": tr["height"],
                   "kind": kind, "transcript": f"daily-social/clips/transcripts/{k}.json", "status": "transcribed",
                   "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        new += 1; print(f"transcribed {name} -> {k} ({kind}, {tr['duration']:.0f}s)")
        SRC.write_text(json.dumps(srcs, indent=1))
    print(f"{new} new recording(s)")


if __name__ == "__main__":
    main()
