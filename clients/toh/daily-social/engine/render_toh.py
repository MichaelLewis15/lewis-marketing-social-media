#!/usr/bin/env python3
"""Touch of Hope daily graphic engine.

Usage:  python3 render_toh.py spec.json OUT_DIR
Writes  OUT_DIR/<date>.png      1080x1350 (4:5, Facebook + Instagram)
        OUT_DIR/gbp/<date>.png  1200x900  (4:3, Google Business Profile)
and prints a JSON report: {"ok": bool, "warnings": [...], "files": [...]}.

Spec (JSON):
{
  "date": "2026-11-03",                 # file name
  "layout": "verse" | "list" | "question",
  "eyebrow": "Tuesday encouragement",   # short, shown in gold caps
  "headline": "Be still<br>and <em>know.</em>",   # <br> and <em> allowed; <em> = gold italic
  "sub": "One short supporting line.",  # optional
  "items": ["A devotional", "A journal"],          # list layout: 3-5 short items (no emojis)
  "verse": {"text": "Be still, and know that I am God.", "ref": "Psalm 46:10 · NKJV"},  # optional on list/question
  "art": "open_book",   # one of: sunrise big_sun open_book mug gift open_box kids candles dove envelope lantern
                        #         star door memorial_candle magnifier book_stack flag leaf wheat bag
  "pill": "Free gift wrapping",          # optional small badge
  "footRight": "Open Mon–Sat · <b>Sheldon, Iowa</b><br>touchofhopesheldon.com",  # optional
  "bg": "cream" | "sage" | "dawn"        # optional background mood
}
Keep headline to about 4-7 words and every item under ~32 characters; the engine shrinks text to fit and
reports any overlap it cannot fix. Always LOOK at both PNGs before using them.
Needs: pip install playwright (Chromium: /opt/pw-browsers or `playwright install chromium` locally).
"""
import json, os, sys, asyncio
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art  # noqa: E402

FONTS = "file://" + os.path.join(HERE, "fonts")
LOGO = "file://" + os.path.join(HERE, "logo.png")

CSS = f"""
@font-face{{font-family:Playfair;src:url({FONTS}/PlayfairDisplay_700Bold.ttf);font-weight:700}}
@font-face{{font-family:Playfair;src:url({FONTS}/PlayfairDisplay_700Bold_Italic.ttf);font-weight:700;font-style:italic}}
@font-face{{font-family:Lora;src:url({FONTS}/Lora_500Medium_Italic.ttf);font-style:italic;font-weight:500}}
@font-face{{font-family:Nunito;src:url({FONTS}/NunitoSans_600SemiBold.ttf);font-weight:600}}
@font-face{{font-family:Nunito;src:url({FONTS}/NunitoSans_700Bold.ttf);font-weight:700}}
@font-face{{font-family:Nunito;src:url({FONTS}/NunitoSans_800ExtraBold.ttf);font-weight:800}}
@font-face{{font-family:Script;src:url({FONTS}/DancingScript_700Bold.ttf)}}
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--f:#2c4a3e;--s:#8fae95;--sl:#e4ece4;--g:#c79a45;--gl:#f0dcae;--c:#fbf6ee;--ink:#25302b;--mut:#5f6b64}}
.c{{position:relative;overflow:hidden;background:var(--c);color:var(--ink);font-family:Nunito,sans-serif}}
.portrait{{width:1080px;height:1350px}}
.land{{width:1200px;height:900px}}
.grain{{position:absolute;inset:0;opacity:.35;pointer-events:none;mix-blend-mode:multiply}}
.blob{{position:absolute;border-radius:50%}}
.txt{{position:absolute}}
.portrait .txt{{left:80px;top:84px;width:var(--tw,600px)}}
.land .txt{{left:72px;top:66px;width:var(--tw,620px)}}
.eyebrow{{font:800 22px/1.2 Nunito;letter-spacing:.24em;text-transform:uppercase;color:var(--g);display:flex;align-items:center;gap:18px}}
.eyebrow::after{{content:"";height:2px;width:80px;flex:none;background:var(--g);opacity:.7}}
h1{{font-family:Playfair;font-weight:700;color:var(--f);letter-spacing:-.01em;line-height:1.04;margin-top:26px}}
h1 em{{font-style:italic;color:var(--g)}}
.sub{{font-size:32px;line-height:1.35;color:var(--mut);margin-top:22px}}
.land .sub{{font-size:28px}}
.list{{margin-top:32px;display:flex;flex-direction:column}}
.li{{display:flex;align-items:center;gap:22px;padding:15px 0;border-bottom:2px solid #2c4a3e14;font:700 31px/1.22 Nunito;color:var(--ink)}}
.land .li{{font-size:27px;padding:11px 0}}
.li:last-child{{border-bottom:0}}
.n{{flex:none;width:54px;height:54px;border-radius:50%;background:var(--f);color:#fff;display:grid;place-items:center;font:800 25px Nunito}}
.land .n{{width:46px;height:46px;font-size:22px}}
.art{{position:absolute;display:flex;justify-content:center;align-items:center}}
.verse{{position:absolute;background:#fff;border-radius:22px;padding:28px 36px 26px 40px;box-shadow:0 10px 40px #2c4a3e14;border-left:6px solid var(--g)}}
.verse q{{quotes:none;font:italic 500 var(--vs,31px)/1.42 Lora;color:var(--f)}}
.verse .ref{{display:block;margin-top:12px;font:800 18px/1 Nunito;letter-spacing:.2em;text-transform:uppercase;color:var(--g)}}
.pill{{position:absolute;background:var(--g);color:#fff;font:800 23px/1 Nunito;letter-spacing:.04em;padding:15px 24px;border-radius:999px;white-space:nowrap}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:150px;display:flex;align-items:center;justify-content:space-between;padding:0 80px;background:var(--f);color:#fff}}
.land .foot{{height:124px;padding:0 72px}}
.foot::before{{content:"";position:absolute;left:0;right:0;top:-34px;height:36px;background:var(--f);clip-path:path('M0 36 C 300 0 700 0 1080 30 V36Z')}}
.land .foot::before{{clip-path:path('M0 36 C 330 0 780 0 1200 30 V36Z')}}
.mark{{display:flex;align-items:center;gap:18px}}
.logo{{height:96px;width:auto;display:block;filter:drop-shadow(0 2px 6px #0004)}}
.land .logo{{height:82px}}
.word{{font:52px/1 Script;color:#fff}}
.land .word{{font-size:46px}}
.word small{{display:block;font:700 15px/1 Nunito;letter-spacing:.22em;text-transform:uppercase;color:var(--gl);margin-top:8px}}
.addr{{text-align:right;font:600 22px/1.45 Nunito;color:#dfe9e0}}
.land .addr{{font-size:20px}}
.addr b{{color:var(--gl);font-weight:800}}
"""
GRAIN = '<svg class="grain" width="100%" height="100%"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .55  0 0 0 0 .5  0 0 0 0 .4  0 0 0 .18 0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>'
BG = {
    "cream": "",
    "sage": "background:linear-gradient(180deg,#eef3ec 0%,#fbf6ee 75%)",
    "dawn": "background:linear-gradient(180deg,#f6dba6 0%,#f3d29c 30%,#fbf6ee 72%)",
}
ARTS = {k: getattr(art, k) for k in ["sunrise", "big_sun", "open_book", "mug", "gift", "open_box", "kids", "candles", "dove",
                                     "envelope", "lantern", "star", "door", "memorial_candle", "magnifier", "book_stack", "flag",
                                     "leaf", "wheat", "bag"]}

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rich(s):
    # allow only <br>, <em>, </em>, <b>, </b>
    t = esc(s)
    for tag in ["br", "em", "/em", "b", "/b"]:
        t = t.replace("&lt;" + tag + "&gt;", "<" + tag + ">").replace("&lt;" + tag + "/&gt;", "<" + tag + ">")
    return t

def foot(right):
    right = right or "915 3rd Ave · <b>Sheldon, Iowa</b><br>touchofhopesheldon.com"
    return (f'<div class="foot"><div class="mark"><img class="logo" src="{LOGO}" alt=""><div class="word">Touch of Hope'
            f'<small>Christian Books &amp; Gifts</small></div></div><div class="addr">{rich(right)}</div></div>')

def build(spec, kind):
    land = kind == "land"
    W, H = (1200, 900) if land else (1080, 1350)
    footH = 124 if land else 150
    layout = spec.get("layout", "verse")
    a = ARTS.get(spec.get("art") or "", None)
    v = spec.get("verse") or None
    items = spec.get("items") or []
    tw = 640 if land else (560 if (a and layout == "list") else 920)
    blobs = ('<div class="blob" style="left:%dpx;top:-150px;width:560px;height:560px;background:#f0dcae;opacity:.5"></div>'
             '<div class="blob" style="left:-200px;top:%dpx;width:420px;height:420px;background:#e4ece4;opacity:.9"></div>') % (W - 420, H - 620)
    txt = f'<div class="txt" id="txt" style="--tw:{tw}px">'
    txt += f'<div class="eyebrow">{esc(spec.get("eyebrow", ""))}</div>'
    txt += f'<h1 id="h1">{rich(spec.get("headline", ""))}</h1>'
    if spec.get("sub"):
        txt += f'<p class="sub">{rich(spec["sub"])}</p>'
    if layout == "list" and items:
        txt += '<div class="list">' + "".join(f'<div class="li"><span class="n">{i + 1}</span><span>{esc(t)}</span></div>' for i, t in enumerate(items[:5])) + '</div>'
    txt += '</div>'
    # art placement
    art_html = ""
    if a:
        if land:
            art_html = f'<div class="art" id="art" style="right:70px;top:150px;width:400px;height:400px">{a(380)}</div>'
        elif layout == "verse":
            art_html = f'<div class="art" id="art" style="left:0;right:0;top:470px;height:420px">{a(440)}</div>'
        elif layout == "list":
            art_html = f'<div class="art" id="art" style="right:50px;top:430px;width:360px;height:360px">{a(330)}</div>'
        else:
            top = 600 if not v else 560
            art_html = f'<div class="art" id="art" style="left:0;right:0;top:{top}px;height:{360 if v else 460}px">{a(360 if v else 460)}</div>'
    pill = ""
    if spec.get("pill"):
        pill = (f'<div class="pill" id="pill" style="right:{70 if land else 60}px;top:{560 if land else 830}px">{esc(spec["pill"])}</div>')
    verse = ""
    if v:
        vt, vr = esc(v.get("text", "")), esc(v.get("ref", ""))
        if land:
            verse = f'<div class="verse" id="verse" style="left:72px;width:{640 if a else 1056}px;bottom:{footH + 40}px;--vs:26px"><q>“{vt}”</q><span class="ref">{vr}</span></div>'
        else:
            verse = f'<div class="verse" id="verse" style="left:80px;right:80px;bottom:{footH + 44}px"><q>“{vt}”</q><span class="ref">{vr}</span></div>'
    body = blobs + txt + art_html + pill + verse + foot(spec.get("footRight"))
    bg = BG.get(spec.get("bg", "cream"), "")
    return (f"<!doctype html><html><head><meta charset=utf-8><style>{CSS}</style></head><body>"
            f"<div class='c {kind}' id='c' style='{bg}'>{GRAIN}{body}</div></body></html>"), W, H

FIT_JS = """
async (start) => {
  await document.fonts.ready;
  const $ = id => document.getElementById(id);
  const h1 = $('h1'), txt = $('txt'), verse = $('verse'), art = $('art'), pill = $('pill'), c = $('c');
  const foot = c.querySelector('.foot');
  const R = e => e ? e.getBoundingClientRect() : null;
  const limitBottom = () => { const ends = [R(foot).top - 30]; if (verse) ends.push(R(verse).top - 26); return Math.min(...ends); };
  let size = start; h1.style.fontSize = size + 'px';
  // headline: shrink until it fits in 3 lines and the text block clears the verse/footer
  for (let i = 0; i < 40; i++) {
    const lines = Math.round(h1.getBoundingClientRect().height / (size * 1.04));
    if (lines <= 3 && R(txt).bottom <= limitBottom()) break;
    size -= 3; h1.style.fontSize = size + 'px';
    if (size < 46) break;
  }
  // verse text: shrink if the verse box would run into the text block
  if (verse) { let vs = parseFloat(getComputedStyle(verse).getPropertyValue('--vs')) || 31;
    for (let i = 0; i < 12 && R(verse).top < R(txt).bottom + 20; i++) { vs -= 1.5; verse.style.setProperty('--vs', vs + 'px'); } }
  const ov = (a, b) => a && b && !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
  const warn = [];
  if (R(txt).bottom > limitBottom() + 2) warn.push('text runs into the verse or footer');
  if (ov(R(art), R(txt))) warn.push('art overlaps the text');
  if (ov(R(art), R(verse))) warn.push('art overlaps the verse');
  if (ov(R(pill), R(txt)) || ov(R(pill), R(verse))) warn.push('badge overlaps text');
  if (size < 52) warn.push('headline had to shrink a lot; shorten it');
  return {size, warn};
}
"""

async def render(spec, out):
    from playwright.async_api import async_playwright
    date = spec["date"]
    os.makedirs(os.path.join(out, "gbp"), exist_ok=True)
    report = {"ok": True, "warnings": [], "files": []}
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    async with async_playwright() as p:
        kw = {"executable_path": exe} if exe else {}
        try:
            b = await p.chromium.launch(**kw)
        except Exception:
            b = await p.chromium.launch()
        for kind, path, start in [("portrait", os.path.join(out, f"{date}.png"), 104), ("land", os.path.join(out, "gbp", f"{date}.png"), 80)]:
            html, W, H = build(spec, kind)
            pg = await b.new_page(viewport={"width": W, "height": H})
            tmp = os.path.join(HERE, f".render-{kind}.html")
            open(tmp, "w").write(html)
            await pg.goto("file://" + tmp, wait_until="load")
            r = await pg.evaluate(FIT_JS, start)
            await pg.screenshot(path=path, clip={"x": 0, "y": 0, "width": W, "height": H})
            await pg.close()
            os.remove(tmp)
            report["files"].append(path)
            report["warnings"] += [f"{kind}: {w}" for w in r["warn"]]
        await b.close()
    report["ok"] = not report["warnings"]
    return report

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    print(json.dumps(asyncio.run(render(spec, out)), indent=1))
