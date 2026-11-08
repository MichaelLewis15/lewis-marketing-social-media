import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from video import Reel, WHITE, BLUE, GRAY
OUT = "/tmp/claude-0/novx"; os.makedirs(OUT, exist_ok=True)
h = lambda t, c=WHITE, s=120, w=800: ("h", w, s, c, t)
b = lambda t, c=GRAY, s=48, w=600: ("b", w, s, c, t)
def step(n, t, sub):
    return dict(beats=6, lines=[("pill", n, 60, BLUE), ("gap", 20), h(t, WHITE, 104), ("gap", 6), b(sub, GRAY, 50)])
scenes = [
    dict(beats=4, lines=[("pill", "AI SEARCH NEWS", 54, BLUE), ("gap", 20), h("ChatGPT is testing", WHITE, 104), h("business profiles.", BLUE, 112)]),
    dict(beats=5, lines=[h("Like a Google", WHITE, 110), h("Business Profile,", WHITE, 104), h("inside ChatGPT.", BLUE, 110), ("gap", 12), b("Spotted in testing. Not launched yet.", GRAY, 48)]),
    dict(beats=5, lines=[b("Early reports: owners could", WHITE, 52), ("gap", 10), h("Claim it.", WHITE, 112), h("Update it.", WHITE, 112), h("Track clicks.", BLUE, 112)]),
    dict(beats=4, lines=[h("Get ready now.", WHITE, 116), ("gap", 10), b("4 things that already help in AI search", GRAY, 48)]),
    step("01", "Complete your Google profile", "Hours, services, photos, all current."),
    step("02", "One page per service", "Give AI a clear page to point to."),
    step("03", "Answer real questions", "The ones customers ask you every week."),
    step("04", "Keep earning reviews", "Fresh, steady, and replied to."),
    dict(beats=6, lines=[h("Follow for", WHITE, 116), h("the launch.", BLUE, 130), ("gap", 10), b("We'll show you how to claim yours", WHITE, 46), ("gap", 8), b("lewismarketingoc.com", GRAY, 42)]),
]
r = Reel(scenes, music=2)
if os.environ.get("MODE") == "--stills":
    for k, t0 in enumerate(r.t0s): r.frame(t0 + 0.7).save(f"{OUT}/still-cgpt-{k}.png")
else:
    r.render(f"{OUT}/cgpt-base.mp4", None); print(round(r.duration, 1))
