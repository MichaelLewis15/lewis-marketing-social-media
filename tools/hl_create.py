#!/usr/bin/env python3
"""Create HighLevel Social Planner posts from queue files (Lewis Marketing sub-account only).

Each tools/queue/<name>.json is {"name": str, "requests": [{"key": str, "ch": str, "body": {...create-post body...}}]}.
Posts that already exist (same accounts, same time, same caption start) are not created twice.
Results go to tools/queue/results/<name>.json and the queue file moves to tools/queue/done/.
"""
import json, os, sys, time, glob, pathlib, datetime, shutil
import requests

LOC = "Auzaxxusb4MezZd78QIC"
API = "https://services.leadconnectorhq.com"
tok = os.environ.get("HL_TOKEN") or sys.exit("HL_TOKEN missing")
H = {"Authorization": f"Bearer {tok}", "Version": "2021-07-28", "Accept": "application/json"}
ALLOWED = {  # every account id must belong to Lewis Marketing
    "6675b1152123b76d2cb7ec8d_Auzaxxusb4MezZd78QIC_124357354103962_page",
    "6675b1322123b7346cb7ecc4_Auzaxxusb4MezZd78QIC_17841464797997853", "6974f71315e87de6131f1713_Auzaxxusb4MezZd78QIC_17841400063513065",
    "68d68df020e681b7200fb3ae_Auzaxxusb4MezZd78QIC_24504201975874302_profile", "68d684430fc868ea55121fdf_Auzaxxusb4MezZd78QIC_24650188417974800_profile",
    "6675e2e22123b7a466b82e33_Auzaxxusb4MezZd78QIC_98983841_page", "6675e2e22123b7a466b82e33_Auzaxxusb4MezZd78QIC_hn49b7zgrI_profile",
    "68dc3e3bdc1b7a12e2779aab_Auzaxxusb4MezZd78QIC_did:plc:i3zzvh6smkiehpyclum7joqx_profile",
    "667a3352ceefda726b068695_Auzaxxusb4MezZd78QIC_16686709381460546882",
    "67a286f2eaec938fc59d4a1f_Auzaxxusb4MezZd78QIC_000AlqRhqEhuK7uXTtFJEtx0AUKzfrGtGc_business", "6aec9b753618c2977d914b21_Auzaxxusb4MezZd78QIC_000T0vo8yqq166O6aGY1qWWS5wHosmUap_business",
    "684183bc498afab8fb028089_Auzaxxusb4MezZd78QIC_UCCm2FqNIL0bCzJkjBhVFOYg_profile", "6aec7ace67bad83a8dce3af3_Auzaxxusb4MezZd78QIC_UC5HHW7Um6dk_6M4sfDzdEFw_profile",
}


def call(method, path, **kw):
    for a in range(5):
        r = requests.request(method, API + path, headers=H, timeout=120, **kw)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(4 * (a + 1)); continue
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
        return r.json() if r.text else {}
    raise RuntimeError(f"kept failing {r.status_code}")


def existing(frm, to):
    out, skip = [], 0
    while True:
        d = call("POST", f"/social-media-posting/{LOC}/posts/list", json={"type": "scheduled", "skip": str(skip), "limit": "100", "fromDate": frm, "toDate": to})
        ps = (d.get("results") or {}).get("posts") or []
        out += ps
        if len(ps) < 100: break
        skip += 100
    return out


def sig(b):
    return (tuple(sorted(b.get("accountIds") or [])), b.get("scheduleDate", "")[:16], (b.get("summary") or "")[:80])


def main():
    files = sorted(glob.glob("tools/queue/*.json"))
    if not files:
        print("Nothing queued."); return
    bad = 0
    for f in files:
        q = json.load(open(f)); reqs = q["requests"]; name = q.get("name") or pathlib.Path(f).stem
        dates = sorted(r["body"]["scheduleDate"] for r in reqs)
        frm = (datetime.datetime.fromisoformat(dates[0].replace("Z", "")) - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to = (datetime.datetime.fromisoformat(dates[-1].replace("Z", "")) + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        have = {sig(p): p["_id"] for p in existing(frm, to)}
        res = []
        for r in reqs:
            b = r["body"]
            if not set(b.get("accountIds") or []) <= ALLOWED:
                res.append({**{k: r[k] for k in ("key", "ch")}, "error": "account not in Lewis Marketing allow-list"}); bad += 1; continue
            if b.get("scheduleDate", "") < datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"):
                res.append({"key": r["key"], "ch": r["ch"], "error": "time passed"}); bad += 1; continue
            s = sig(b)
            if s in have:
                res.append({"key": r["key"], "ch": r["ch"], "postId": have[s], "when": b["scheduleDate"], "existed": True}); continue
            try:
                d = call("POST", f"/social-media-posting/{LOC}/posts", json=b)
                pid = ((d.get("results") or {}).get("post") or {}).get("_id") or (d.get("post") or {}).get("_id")
                if not pid: raise RuntimeError("no post id in response: " + json.dumps(d)[:200])
                have[s] = pid
                res.append({"key": r["key"], "ch": r["ch"], "postId": pid, "when": b["scheduleDate"]})
                print("created", r["key"], r["ch"], pid)
            except Exception as e:
                res.append({"key": r["key"], "ch": r["ch"], "error": str(e)[:300]}); bad += 1
                print("FAILED", r["key"], r["ch"], e, file=sys.stderr)
            time.sleep(0.4)
        pathlib.Path(f"tools/queue/results/{name}.json").write_text(json.dumps({"name": name, "at": datetime.datetime.utcnow().isoformat() + "Z", "results": res}, indent=1))
        shutil.move(f, f"tools/queue/done/{pathlib.Path(f).name}")
        print(name, "created/linked", sum(1 for x in res if x.get("postId")), "failed", sum(1 for x in res if x.get("error")))
    if bad: print(f"::warning::{bad} request(s) failed; see tools/queue/results")


if __name__ == "__main__":
    main()
