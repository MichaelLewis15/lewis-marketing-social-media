#!/usr/bin/env python3
# run-trigger: 2026-11-08 20:28 token re-added
"""TikTok video sync for the Lewis Marketing HighLevel sub-account.

TikTok only accepts videos stored in HighLevel Media Storage. Every run:
  1. lists scheduled posts that go to a TikTok account,
  2. for any whose video is NOT on assets.cdn.filesafe.space, uploads that video
     (from this repo when it lives here, otherwise downloaded) into the
     "TikTok videos" folder (reusing a file of the same name if already there),
  3. edits the post so its media points at the HighLevel copy.
Touches nothing else. Lewis Marketing location only.
"""
import json, os, sys, time, mimetypes, datetime, pathlib, urllib.request
import requests

LOC = "Auzaxxusb4MezZd78QIC"
USER = "0T5YzQFGjmXmN5py288b"  # Michael's HighLevel user id
FOLDER = os.environ.get("HL_TIKTOK_FOLDER", "6af11ffa1ac4234dcd04e3de")
API = "https://services.leadconnectorhq.com"
REPO_RAW = "https://raw.githubusercontent.com/MichaelLewis15/lewis-marketing-social-media/main/"
HOSTED = ("https://assets.cdn.filesafe.space/",)
TIKTOK = [
    "67a286f2eaec938fc59d4a1f_Auzaxxusb4MezZd78QIC_000AlqRhqEhuK7uXTtFJEtx0AUKzfrGtGc_business",
    "6aec9b753618c2977d914b21_Auzaxxusb4MezZd78QIC_000T0vo8yqq166O6aGY1qWWS5wHosmUap_business",
]
KEEP = ["accountIds", "summary", "status", "scheduleDate", "type", "createdBy", "userId",
        "followUpComment", "tiktokPostDetails", "youtubePostDetails", "facebookPostDetails",
        "instagramPostDetails", "linkedinPostDetails", "gmbPostDetails", "ogTagsDetails", "tags", "categoryId"]
DRY = os.environ.get("DRY_RUN") == "1"

tok = os.environ.get("HL_TOKEN")
if not tok:
    print("::warning::HL_TOKEN secret is missing. Add it in GitHub: Settings > Secrets and variables > Actions. Skipping this run.")
    sys.exit(0)
H = {"Authorization": f"Bearer {tok}", "Version": "2021-07-28", "Accept": "application/json"}


def call(method, path, **kw):
    for attempt in range(4):
        r = requests.request(method, API + path, headers={**H, **kw.pop("headers", {})}, timeout=300, **kw)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (attempt + 1)); continue
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:400]}")
        return r.json() if r.text else {}
    raise RuntimeError(f"{method} {path} kept failing ({r.status_code})")


def check_location():
    try:
        d = call("GET", f"/locations/{LOC}")
    except RuntimeError as e:
        if "401" in str(e):
            print("Location name check skipped (token has no Locations scope); the token is bound to one sub-account and every call below is pinned to " + LOC)
            return
        raise
    name = ((d.get("location") or d).get("name") or "").strip()
    if "Lewis Marketing" not in name:
        sys.exit(f"Location {LOC} is named {name!r}, not Lewis Marketing. Stopping.")


def scheduled_tiktok_posts():
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    out, skip = [], 0
    while True:
        body = {"type": "scheduled", "accounts": ",".join(TIKTOK), "skip": str(skip), "limit": "100",
                "fromDate": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "toDate": (now + datetime.timedelta(days=120)).strftime("%Y-%m-%dT%H:%M:%S.000Z")}
        d = call("POST", f"/social-media-posting/{LOC}/posts/list", json=body)
        posts = ((d.get("results") or {}).get("posts")) or []
        out += posts
        if len(posts) < 100: break
        skip += 100
    seen, res = set(), []
    for p in posts_unique(out):
        if p["_id"] in seen: continue
        seen.add(p["_id"])
        if p.get("deleted") or p.get("status") != "scheduled": continue
        if not set(p.get("accountIds") or []) & set(TIKTOK): continue
        res.append(p)
    return res


def posts_unique(posts):
    return sorted(posts, key=lambda p: p.get("scheduleDate") or "")


def folder_files():
    files, off = {}, 0
    while True:
        d = call("GET", "/medias/files", params={"altId": LOC, "altType": "location", "type": "file",
                                                  "parentId": FOLDER, "limit": 100, "offset": off,
                                                  "sortBy": "createdAt", "sortOrder": "desc"})
        batch = d.get("files") or []
        for f in batch:
            u = f.get("url") or ""
            if u.startswith(HOSTED) and f.get("name"):
                files.setdefault(f["name"], u)
        if len(batch) < 100: break
        off += 100
    return files


def video_bytes(url):
    if url.startswith(REPO_RAW):
        p = pathlib.Path(url[len(REPO_RAW):])
        if p.is_file():
            return p.read_bytes()
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    return r.content


def upload(name, data):
    files = {"file": (name, data, mimetypes.guess_type(name)[0] or "video/mp4")}
    d = call("POST", "/medias/upload-file", files=files, data={"name": name, "parentId": FOLDER, "hosted": "false"})
    url = d.get("url") or (d.get("data") or {}).get("url")
    if not url:
        raise RuntimeError(f"upload of {name} returned no url: {json.dumps(d)[:300]}")
    return url


def main():
    check_location()
    posts = scheduled_tiktok_posts()
    have = folder_files()
    fixed, ok, failed = [], 0, []
    for p in posts:
        media = p.get("media") or []
        vids = [m for m in media if (m.get("type") or "").startswith("video") or (m.get("url") or "").lower().endswith((".mp4", ".mov"))]
        if not vids: continue
        v = vids[0]
        if (v.get("url") or "").startswith(HOSTED):
            ok += 1; continue
        name = v["url"].split("?")[0].rstrip("/").split("/")[-1]
        when = p.get("scheduleDate")
        try:
            if name in have:
                hl = have[name]
            elif DRY:
                hl = "(would upload)"
            else:
                hl = upload(name, video_bytes(v["url"]))
                have[name] = hl
            body = {k: p[k] for k in KEEP if p.get(k) not in (None, {}, [])}
            body["userId"] = p.get("userId") or p.get("createdBy") or USER
            body.setdefault("createdBy", USER)
            for k in ("tiktokPostDetails",):
                if k in body: body[k] = {a: b for a, b in body[k].items() if b is not None and a != "shortenedLinks"}
            body["media"] = [{**{k: x for k, x in m.items() if k in ("url", "type", "thumbnail", "defaultThumb", "altText", "caption")},
                              **({"url": hl, "type": "video/mp4"} if m is v else {})} for m in media]
            if not DRY:
                call("PUT", f"/social-media-posting/{LOC}/posts/{p['_id']}", json=body)
            fixed.append({"post": p["_id"], "when": when, "video": name, "hl": hl})
            print(f"FIXED {when} {name} -> {hl}")
        except Exception as e:
            failed.append({"post": p["_id"], "when": when, "video": name, "error": str(e)[:300]})
            print(f"FAILED {when} {name}: {e}", file=sys.stderr)
    summary = {"at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z", "checked": len(posts),
               "alreadyHosted": ok, "fixed": fixed, "failed": failed, "dryRun": DRY}
    print(json.dumps(summary, indent=1))
    pathlib.Path("tiktok-sync-result.json").write_text(json.dumps(summary, indent=1))
    if failed: sys.exit(1)


if __name__ == "__main__":
    main()
