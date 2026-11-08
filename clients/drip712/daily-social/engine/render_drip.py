#!/usr/bin/env python3
"""Drip712 graphic engine (IV hydration and wellness, Sheldon, Iowa).

Usage:  python3 render_drip.py spec.json OUT_DIR
Writes  OUT_DIR/<name>.png      1080x1350 (4:5, Facebook + Instagram)
        OUT_DIR/gbp/<name>.png  1200x900  (4:3, Google Business Profile)
Prints  {"ok": bool, "warnings": [...], "files": [...]}.

Spec (JSON):
{
  "name": "2026-11-16",                        # file name (no extension)
  "layout": "list" | "stat" | "question" | "myth" | "greeting",
  "eyebrow": "Meet the menu",                  # short, aqua caps
  "headline": "Which drip is <em>yours?</em>",  # <br>, <em> (aqua italic) and <b> allowed
  "sub": "One short supporting line.",         # optional
  "items": ["Reboot", "Immune Boost"],         # list: 3-5 items, each under ~34 chars. Use "Title|detail" for a two-part item
  "stat": {"big": "0", "label": "vitamin D made by winter sun..."},   # stat layout
  "pairs": [{"myth": "...", "fact": "..."}],  # myth layout, 2-3 pairs
  "art": "drip_bag",   # see art.py: drip_bag droplet snowflake winter_sun shield sparkle battery chair house gift
                       #             calendar heart question leaf clock card party
  "pill": "No house-call fee for 4+",          # optional badge
  "source": "Source: CDC, cdc.gov/flu",        # optional small source line above the footer (required for stats)
  "bg": "cream" | "mist" | "blush" | "navy"    # optional mood
}
Always LOOK at both PNGs. Needs playwright + Chromium (/opt/pw-browsers).
"""
import json, os, sys, asyncio
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art  # noqa: E402

F = "file://" + os.path.join(HERE, "fonts")
CSS = f"""
@font-face{{font-family:Fraunces;src:url({F}/fraunces-latin-400-normal.woff2);font-weight:400}}
@font-face{{font-family:Fraunces;src:url({F}/fraunces-latin-500-normal.woff2);font-weight:500}}
@font-face{{font-family:Fraunces;src:url({F}/fraunces-latin-600-normal.woff2);font-weight:600}}
@font-face{{font-family:Fraunces;src:url({F}/fraunces-latin-400-italic.woff2);font-weight:400;font-style:italic}}
@font-face{{font-family:Fraunces;src:url({F}/fraunces-latin-500-italic.woff2);font-weight:500;font-style:italic}}
@font-face{{font-family:Fraunces;src:url({F}/fraunces-latin-600-italic.woff2);font-weight:600;font-style:italic}}
@font-face{{font-family:DM;src:url({F}/dm-sans-latin-400-normal.woff2);font-weight:400}}
@font-face{{font-family:DM;src:url({F}/dm-sans-latin-500-normal.woff2);font-weight:500}}
@font-face{{font-family:DM;src:url({F}/dm-sans-latin-700-normal.woff2);font-weight:700}}
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--n:#143a4f;--a:#2fa3b2;--al:#bfe6ea;--m:#dff1f2;--c:#fbf8f4;--s:#f1e6da;--b:#f2d9cf;--g:#c3955a;--ink:#1d2b33;--mut:#55656e}}
.c{{position:relative;overflow:hidden;background:var(--c);color:var(--ink);font-family:DM,sans-serif}}
.portrait{{width:1080px;height:1350px}} .land{{width:1200px;height:900px}}
.blob{{position:absolute;border-radius:50%}}
.txt{{position:absolute}}
.portrait .txt{{left:84px;top:96px;width:var(--tw,912px)}}
.land .txt{{left:72px;top:64px;width:var(--tw,640px)}}
.eyebrow{{font:700 22px/1.2 DM;letter-spacing:.26em;text-transform:uppercase;color:var(--a);display:flex;align-items:center;gap:18px}}
.eyebrow::before{{content:"";width:14px;height:18px;flex:none;background:var(--a);clip-path:path('M7 0 C4 6 0 9 0 12 a7 7 0 0 0 14 0 C14 9 10 6 7 0z')}}
.land .eyebrow{{font-size:19px}}
h1{{font-family:Fraunces;font-weight:500;color:var(--n);letter-spacing:-.015em;line-height:1.05;margin-top:24px}}
h1 em{{font-style:italic;color:var(--a);font-weight:500}}
h1 b{{font-weight:600}}
.sub{{font:400 32px/1.4 DM;color:var(--mut);margin-top:22px}}
.land .sub{{font-size:26px;margin-top:16px}}
.list{{margin-top:30px;display:flex;flex-direction:column}}
.li{{display:flex;align-items:center;gap:22px;padding:17px 0;border-bottom:2px solid #143a4f14;font:500 34px/1.22 DM;color:var(--ink)}}
.li:last-child{{border-bottom:0}}
.li small{{display:block;font:400 23px/1.3 DM;color:var(--mut);margin-top:3px}}
.land .li{{font-size:25px;padding:10px 0;gap:18px}} .land .li small{{font-size:19px}}
.n{{flex:none;width:52px;height:52px;border-radius:50%;background:var(--n);color:#fff;display:grid;place-items:center;font:700 23px DM}}
.land .n{{width:42px;height:42px;font-size:19px}}
.stat{{display:flex;align-items:baseline;gap:26px;margin-top:30px}}
.big{{font:500 var(--bs,190px)/0.9 Fraunces;color:var(--a);letter-spacing:-.03em;white-space:nowrap}}
.slab{{font:500 30px/1.32 DM;color:var(--n);max-width:440px}}
.land .slab{{font-size:24px;max-width:300px}}
.pairs{{margin-top:30px;display:flex;flex-direction:column;gap:18px}}
.pair{{background:#fff;border-radius:22px;padding:22px 28px;box-shadow:0 8px 30px #143a4f12}}
.pair .my{{font:500 25px/1.3 DM;color:var(--mut);text-decoration:line-through;text-decoration-color:#c3955a99;text-decoration-thickness:3px}}
.pair .my::before,.pair .fa::before{{display:inline-block;font:700 16px/1 DM;letter-spacing:.18em;padding:6px 10px;border-radius:999px;margin-right:14px;vertical-align:3px;text-decoration:none}}
.pair .my::before{{content:"MYTH";background:var(--s);color:#8a6438}}
.pair .fa{{font:500 28px/1.32 DM;color:var(--n);margin-top:12px}}
.pair .fa::before{{content:"FACT";background:var(--a);color:#fff}}
.land .pair{{padding:14px 20px}} .land .pair .my{{font-size:20px}} .land .pair .fa{{font-size:22px;margin-top:8px}}
.art{{position:absolute;display:flex;justify-content:center;align-items:center}}
.pill{{position:absolute;background:var(--g);color:#fff;font:700 24px/1 DM;letter-spacing:.02em;padding:15px 26px;border-radius:999px;white-space:nowrap;box-shadow:0 8px 20px #c3955a40}}
.land .pill{{font-size:20px;padding:12px 20px}}
.src{{position:absolute;font:400 18px/1.35 DM;color:var(--mut);opacity:.9}}
.land .src{{font-size:15px}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:146px;display:flex;align-items:center;justify-content:space-between;padding:0 84px;background:var(--n);color:#fff}}
.land .foot{{height:118px;padding:0 72px}}
.foot::before{{content:"";position:absolute;left:0;right:0;top:-30px;height:32px;background:var(--n);clip-path:path('M0 32 C 260 0 760 0 1080 26 V32Z')}}
.land .foot::before{{clip-path:path('M0 32 C 300 0 840 0 1200 26 V32Z')}}
.mark{{display:flex;align-items:center;gap:16px}}
.drop{{width:40px;height:52px;background:var(--a);clip-path:path('M20 0 C12 16 0 26 0 33 a20 20 0 0 0 40 0 C40 26 28 16 20 0z')}}
.land .drop{{width:34px;height:44px;clip-path:path('M17 0 C10 14 0 22 0 28 a17 17 0 0 0 34 0 C34 22 24 14 17 0z')}}
.word{{font:500 54px/1 Fraunces;letter-spacing:-.02em;color:#fff}}
.word span{{color:var(--al)}}
.land .word{{font-size:46px}}
.word small{{display:block;font:500 15px/1 DM;letter-spacing:.3em;text-transform:uppercase;color:var(--al);margin-top:9px}}
.addr{{text-align:right;font:400 22px/1.5 DM;color:#d5e6ea}}
.land .addr{{font-size:19px}}
.addr b{{color:#fff;font-weight:700}}
.navy{{background:var(--n)!important}} .navy h1,.navy .slab,.navy .li{{color:#fff}} .navy .sub,.navy .src,.navy .li small{{color:#c9dde2}}
.navy .li{{border-color:#ffffff22}} .navy .n{{background:var(--a)}}
.center .txt{{text-align:center}} .center .eyebrow{{justify-content:center}}
"""
BG = {"cream": "", "mist": "background:linear-gradient(180deg,#e3f3f4 0%,#fbf8f4 70%)",
      "blush": "background:linear-gradient(180deg,#f6e3db 0%,#fbf8f4 70%)", "navy": ""}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rich(s):
    t = esc(s)
    for tag in ["br", "em", "/em", "b", "/b"]:
        t = t.replace("&lt;" + tag + "&gt;", "<" + tag + ">").replace("&lt;" + tag + "/&gt;", "<" + tag + ">")
    return t


def foot():
    return ('<div class="foot"><div class="mark"><div class="drop"></div><div class="word">drip <span>712</span>'
            '<small>Wellness from within</small></div></div>'
            '<div class="addr">101 Runger Ave N, Suite G<br><b>Sheldon, Iowa</b> · drip712.com</div></div>')


def build(spec, kind):
    land = kind == "land"
    W, H = (1200, 900) if land else (1080, 1350)
    footH = 118 if land else 146
    lay = spec.get("layout", "list")
    a = art.ARTS.get(spec.get("art") or "")
    items = spec.get("items") or []
    bgk = spec.get("bg", "cream")
    center = lay in ("question", "greeting") and not land
    # text width
    if land:
        tw = 660 if a else 1056
        if lay == "myth":
            tw = 1056 if not a else 720
    else:
        tw = 590 if (a and lay in ("list",)) else 912
    blobs = ""
    if bgk != "navy":
        blobs = (f'<div class="blob" style="left:{W-380}px;top:-170px;width:560px;height:560px;background:#dff1f2;opacity:.75"></div>'
                 f'<div class="blob" style="left:-220px;top:{H-640}px;width:440px;height:440px;background:#f2d9cf;opacity:.55"></div>')
    else:
        blobs = (f'<div class="blob" style="left:{W-380}px;top:-170px;width:560px;height:560px;background:#2fa3b2;opacity:.18"></div>')
    t = f'<div class="txt" id="txt" style="--tw:{tw}px">'
    t += f'<div class="eyebrow">{esc(spec.get("eyebrow", ""))}</div>'
    if lay == "stat":
        st = spec.get("stat") or {}
        t += f'<div class="stat"><div class="big" id="big">{esc(st.get("big", ""))}</div><div class="slab">{rich(st.get("label", ""))}</div></div>'
    t += f'<h1 id="h1">{rich(spec.get("headline", ""))}</h1>'
    if spec.get("sub"):
        t += f'<p class="sub">{rich(spec["sub"])}</p>'
    if lay == "list" and items:
        rows = []
        for i, it in enumerate(items[:5]):
            head, _, det = str(it).partition("|")
            rows.append(f'<div class="li"><span class="n">{i+1}</span><span>{esc(head)}{"<small>"+esc(det)+"</small>" if det else ""}</span></div>')
        t += '<div class="list">' + "".join(rows) + '</div>'
    if lay == "myth":
        t += '<div class="pairs">' + "".join(f'<div class="pair"><div class="my">{esc(p["myth"])}</div><div class="fa">{esc(p["fact"])}</div></div>' for p in (spec.get("pairs") or [])[:3]) + '</div>'
    t += '</div>'
    ah = ""
    if a:
        if land:
            if lay == "myth":
                ah = f'<div class="art" id="art" style="right:40px;top:70px;width:340px;height:340px">{a(300)}</div>'
            else:
                ah = f'<div class="art" id="art" style="right:64px;top:150px;width:400px;height:420px">{a(370)}</div>'
        elif lay == "list":
            ah = f'<div class="art" id="art" style="right:28px;top:520px;width:370px;height:420px">{a(340)}</div>'
        elif lay in ("question", "greeting"):
            ah = f'<div class="art" id="art" style="left:0;right:0;bottom:{footH+130}px;height:440px">{a(430)}</div>'
        elif lay == "stat":
            ah = f'<div class="art" id="art" style="right:50px;bottom:{footH+90}px;width:330px;height:330px">{a(300)}</div>'
        elif lay == "myth":
            ah = ""
    pill = ""
    if spec.get("pill"):
        if land:
            pill = f'<div class="pill" id="pill" style="right:72px;bottom:{footH+70}px">{esc(spec["pill"])}</div>'
        else:
            pill = f'<div class="pill" id="pill" style="{"left:50%;transform:translateX(-50%)" if center else "left:84px"};bottom:{footH+80}px">{esc(spec["pill"])}</div>'
    src = ""
    if spec.get("source"):
        src = f'<div class="src" id="src" style="left:{72 if land else 84}px;right:{72 if land else 84}px;bottom:{footH+(30 if land else 40)}px">{rich(spec["source"])}</div>'
    cls = f"c {kind}" + (" navy" if bgk == "navy" else "") + (" center" if center else "")
    body = blobs + t + ah + pill + src + foot()
    return (f"<!doctype html><html><head><meta charset=utf-8><style>{CSS}</style></head><body>"
            f"<div class='{cls}' id='c' style='{BG.get(bgk, '')}'>{body}</div></body></html>"), W, H


FIT_JS = """
async (start) => {
  await document.fonts.ready;
  const $ = id => document.getElementById(id);
  const h1=$('h1'), txt=$('txt'), art=$('art'), pill=$('pill'), src=$('src'), big=$('big'), c=$('c');
  const foot=c.querySelector('.foot');
  const R=e=>e?e.getBoundingClientRect():null;
  const ov=(a,b)=>a&&b&&!(a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom);
  const floor=()=>{const ends=[R(foot).top-24];if(src)ends.push(R(src).top-14);if(pill&&!c.classList.contains('land'))ends.push(R(pill).top-16);if(art&&R(art).left<R(txt).right-40&&R(art).top>R(txt).top+60)ends.push(R(art).top+20);return Math.min(...ends)};
  let size=start; h1.style.fontSize=size+'px';
  if(big){let bs=parseFloat(getComputedStyle(big).fontSize);for(let i=0;i<30&&big.scrollWidth>txt.clientWidth*0.55;i++){bs-=8;big.style.setProperty('--bs',bs+'px')}}
  for(let i=0;i<50;i++){
    const lines=Math.round(h1.getBoundingClientRect().height/(size*1.05));
    if(lines<=3 && R(txt).bottom<=floor()) break;
    size-=3; h1.style.fontSize=size+'px';
    if(size<40) break;
  }
  // shrink list/pairs if still overflowing
  let k=1; const rows=[...c.querySelectorAll('.li,.pair')];
  for(let i=0;i<14&&R(txt).bottom>floor()&&rows.length;i++){k-=0.04;rows.forEach(r=>r.style.zoom=k)}
  // portrait: grow short content so the card doesn't look empty
  {
    const max=start*(c.classList.contains('portrait')?1.3:1.25);
    for(let i=0;i<40&&size<max;i++){size+=3;h1.style.fontSize=size+'px';const lines=Math.round(h1.getBoundingClientRect().height/(size*1.05));if(lines>3||R(txt).bottom>floor()-50){size-=3;h1.style.fontSize=size+'px';break}}
    if(k===1&&rows.length){for(let i=0;i<10;i++){k+=0.04;rows.forEach(r=>r.style.zoom=k);if(R(txt).bottom>floor()-40){k-=0.04;rows.forEach(r=>r.style.zoom=k);break}}}
  }
  const warn=[];
  if(R(txt).bottom>floor()+2) warn.push('text runs into the art, badge, source or footer');
  if(art&&ov(R(art),R(txt))&&R(art).top<R(txt).bottom-30&&R(art).left<R(txt).right-30) warn.push('art overlaps the text');
  if(pill&&(ov(R(pill),R(txt))||ov(R(pill),R(art)))) warn.push('badge overlaps text or art');
  if(size<48) warn.push('headline had to shrink a lot; shorten it');
  return {size,warn};
}
"""


async def render(spec, out):
    from playwright.async_api import async_playwright
    name = spec.get("name") or spec["date"]
    os.makedirs(os.path.join(out, "gbp"), exist_ok=True)
    rep = {"ok": True, "warnings": [], "files": []}
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    async with async_playwright() as p:
        try:
            b = await p.chromium.launch(**({"executable_path": exe} if exe else {}))
        except Exception:
            b = await p.chromium.launch()
        kinds = [("portrait", os.path.join(out, f"{name}.png"), spec.get("size", 96))]
        if not spec.get("noGbp"):
            kinds.append(("land", os.path.join(out, "gbp", f"{spec.get('gbpName') or name}.png"), spec.get("landSize", 72)))
        for kind, path, start in kinds:
            html, W, H = build(spec, kind)
            pg = await b.new_page(viewport={"width": W, "height": H})
            tmp = os.path.join(HERE, f".render-{kind}-{os.getpid()}.html")
            open(tmp, "w").write(html)
            await pg.goto("file://" + tmp, wait_until="load")
            r = await pg.evaluate(FIT_JS, start)
            await pg.screenshot(path=path, clip={"x": 0, "y": 0, "width": W, "height": H})
            await pg.close()
            os.remove(tmp)
            rep["files"].append(path)
            rep["warnings"] += [f"{kind}: {w}" for w in r["warn"]]
        await b.close()
    rep["ok"] = not rep["warnings"]
    return rep


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    specs = spec if isinstance(spec, list) else [spec]
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    for s in specs:
        print(json.dumps({"name": s.get("name") or s.get("date"), **asyncio.run(render(s, out))}))
