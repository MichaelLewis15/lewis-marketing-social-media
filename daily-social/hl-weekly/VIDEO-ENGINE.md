# Lewis Marketing video engine

One renderer for every Lewis Marketing video made from text: HighLevel Weekly, launches, tips, myth vs fact, before and after, stats, client reviews, podcast promos, countdowns and the monthly results recap. Code: `engine.py` (spec format in its docstring), entry point `render_weekly.py`, voiceover `voice.py`.

## Michael's rules (Nov 14, 2026)
- **Mix the looks.** Never the same `style` twice in a row (see Rotation).
- **Fresh designs (Michael, Nov 15, 2026).** The old dark-navy reel template (Howie bottom left with a "Hi, I'm Howie!" bubble) is retired: every Lewis Marketing video is made with this engine. Lean on `light`, `bold` and `cards` (and the seasonal looks); use `navy` at most once in every four videos. Set `itemWord` on list videos in the `bold` look so the label fits the topic (TIP, STEP, IDEA) instead of UPDATE.
- **Howie is optional.** Keep him in most videos. Set `"howie": false` when the look carries the video on its own (`bold` works well without him) or the topic is serious. Never two videos in a row without him.
- **Voiceover must sound professional and say every word correctly.** Use `"voice": true` with the default voice `af_heart`. After every voiced render, read `voice-check.json` in the output folder: every scene must have `"ok": true`. If a scene is flagged, look at its `diffs`; if a word was said wrong, add a respelling to `LEXICON` in `voice.py` (never change the on-screen text) and render again. Brand words already covered: HighLevel, GoHighLevel, ChatGPT, OpenAI, AI, SEO, CRM, GBP, SMS, API, ROI, DNS, lewismarketingoc.com, web addresses, Sioux, Le Mars, Drip712, percentages, month abbreviations, number ranges.
- **Captions** are on whenever the voice is on (`"captions": false` to turn them off). They show the on-screen spelling, one short phrase at a time, the spoken word highlighted.
- No emojis in on-screen text or post copy. Statistics only from credible sources: the `stat` format refuses a stat without `source`, shows it on screen, and the post's first comment carries the link (`url`).
- Results recap (`results` format): numbers are combined across clients. Never name, describe or hint at a specific client, and never show one client's number on its own.

## Formats (`"format"`)
| format | use it for | content keys |
|---|---|---|
| `list` (default) | weekly recaps, launches, 3-5 tips | `items[{title, why, tag}]` |
| `myth` | Myth Monday | `items[{myth, fact}]` (1-4); the fact appears as the narrator says "Fact" |
| `beforeafter` | what changes with a service | `before{title, points[]}`, `after{title, points[]}` |
| `stat` | Stat Snack, research | `stats[{value, label, source, url}]` (1-4) |
| `results` | monthly results recap | `month`, `stats[{value, label}]`, optional `footnote` |
| `review` | client love | `reviews[{text, name, stars, source}]`: real reviews only, copied exactly, first name and last initial |
| `podcast` | The Marketing Lens promos | `episode{show, number, title, guest, quote}`; optional `audio` (a clip; the waveform follows it and the narrator stays quiet on that scene) |
| `countdown` | events, Small Business Saturday | `event{name, date, time, place}`, `postDate` (the day it posts) |
Shared keys: `eyebrow`, `head1`, `head2`, `week` (subtitle), `sub2`, `cta`, `cta2`, `button`, `gbpTitle`, `music` (0-3, rotate). Each format has sensible defaults for the intro words; override any of them.

## Looks (`"style"`)
Rotation: `navy` (dark navy, big numbers) -> `light` (Clean: off-white page, navy type, highlighter) -> `bold` (Color block: full-screen brand color wipes, giant numerals) -> `cards` (white cards stacking on navy) -> back to `navy`. Pick the next one after the style of the most recent video spec (in `daily-social/video-specs/` and `daily-social/hl-weekly/specs/`, newest by date; no `style` means `navy`). If `dsconfig/settings.videoLooks` (written by the weekly social sync) says a look is clearly behind the others, skip it once and use the next.
Seasonal looks replace the rotation in their window, still never twice in a row: `shopsmall` (red awning, cream) the week of Small Business Saturday; `holiday` (Santa-hat Howie, red and gold) Dec 1 to Dec 24; `yearend` (gold on midnight, party-hat Howie) Dec 26 to Jan 3. Veterans Day stays promotion-free in any look.

## Sizes (`"sizes"`, default all four)
`916` 1080x1920 (Instagram and Facebook Reels, TikTok, Threads, YouTube Shorts), `169` 1920x1080 (YouTube, LinkedIn, Bluesky), `45` 1080x1350 (Instagram and Facebook feed, LinkedIn feed), `11` 1080x1080 (square feeds, Google-friendly). Outputs per size: `v<size>.mp4`, `cover<size>.jpg`; plus `gbp.png` (1200x900) for Google Business Profile.

## Rendering
- **In the cloud (preferred):** save the spec as `daily-social/video-specs/<YYYY-MM-DD>-<slot or name>.json` with `"out": "daily/video/<same name>"` and push. The "Render videos" GitHub Action renders it, commits the files into `out`, and writes `tools/render/results/<spec name>.json` ({ok, seconds, files with content hashes, voiceCheck}). Pull and check `ok` and `voiceCheck.ok` before using the files. HighLevel Weekly specs in `daily-social/hl-weekly/specs/` render the same way when they have `out`.
- **Locally:** `pip install --break-system-packages kokoro-onnx soundfile faster-whisper` once, `git clone --depth 1 -b models <repo url> daily-social/models` once (voice models; Hugging Face is blocked from the container), then `TMPDIR=/tmp python3 daily-social/hl-weekly/render_weekly.py spec.json OUTDIR`. Without `"voice"` the models are not needed.
- **Quick check:** `python3 daily-social/hl-weekly/render_weekly.py --preview spec.json OUTDIR [916,169]` writes a still of every scene and `gbp.png` in seconds. Look at them before a full render: no text cut off, nothing behind Howie.

## Quality check (before anything posts)
Every cloud render runs `tools/qc.py dir <out>` and stores the result as `qc` in `tools/render/results/<name>.json`; a qc error makes `ok` false. It checks size, codec, frame rate, length (9:16 at most 180 s), loudness (both renderers now finish at about -14 LUFS with a limiter), black or silent openings and the 9:16 safe zones. Before any post is scheduled (by a task or the hub), run `python3 tools/qc.py copy posts.json` on the copy: emojis, "Piper Financial Group" in full, "The Marketing Lens", stats without a source link, platform length limits and Instagram's 5-hashtag limit are errors or warnings there. Fix errors; never schedule around them.

## Posting
- Save the hub daily doc with `asset: {type:"video", file:<raw url v916.mp4>, poster:<raw url cover916.jpg>, gbp:<raw url gbp.png>, note:"16:9: <raw url v169.mp4> · 4:5: <raw url v45.mp4> · 1:1: <raw url v11.mp4>", style, format, howie:true|false, voice:true|false, spec:<repo path of the spec>, specData:<the spec JSON>}`. `spec` and `specData` let Michael edit the video from the hub's Video studio.
- Channel map: 9:16 to Facebook reel, Instagram reel (both accounts), Threads (both), TikTok (both), YouTube Shorts; 16:9 to LinkedIn (both), Bluesky, YouTube regular video; 4:5 to Instagram and Facebook feed posts when the post is a feed post instead of a reel; `gbp.png` to Google Business.
- TikTok: commit the video before creating the post; the TikTok sync names each Media Storage copy after its full repo path (and `?v=` version), so files never collide.

## Re-render requests (hub Video studio)
Michael edits a video in the hub; the page saves collection `rerender` doc {id, dailyId, specPath, spec, status:"requested"}. The **video-rerender** scheduled task (every two hours, 7 AM to 9 PM) processes them:
1. Set status `working`. Check the new spec (no emojis, stats keep sources, results never name a client). Write it to `specPath` keeping its `out`, commit, push, and wait for `tools/render/results/<name>.json` with a newer `at` (pull every minute, up to 40 minutes).
2. If `ok` and `voiceCheck.ok` (when voiced): new version id = the first 8 characters of the v916.mp4 hash in the results file. For every channel in hub `hl` doc `p<dailyId>` whose post is still scheduled, edit-post (full body + userId) with the media URL swapped for the new raw URL plus `?v=<version>` (9:16, 16:9, 4:5 or gbp.png as before). TikTok posts get the raw URL too; the TikTok sync re-hosts that version in Media Storage within 30 minutes. Update the daily doc's asset URLs, style, howie, voice and specData. Status `done` with a one-line note.
3. On any failure: status `failed` with the reason; touch nothing in HighLevel.

## Monthly results recap
Superseded Nov 22, 2026: the **monthly-client-recap** task now posts the recap on the 1st (graphic plus 16:9 and 9:16 videos; rules in daily-social/SKILL.md, "Monthly Client Results recap"). The old notes below are kept for reference only.
The **results-recap** scheduled task (paused) ran on the 2nd of each month for the month before. Read only in HighLevel: for every client sub-account (list_locations, all pages), skipping Lewis Marketing itself, templates, test accounts, Michael's own businesses and any id in `dsconfig/settings.resultsExclude`, count new pipeline leads (search-opportunities-advanced, `date_added` in the month, `total`), deals won (`status` won and `lastStatusChangeAt` in the month) and new contacts (search-contacts-advanced, `dateAdded` in the month, `total`). Sum them, never keep per-client rows in the spec, the post or the hub. Build a `results` spec with only the combined totals that are large enough to be meaningful (skip a number under 10), render it, and save a hub daily doc with status `review`: Michael approves it before anything is scheduled.

## 9:16 safe zone (Michael's rule, Nov 25, 2026)
Every tall (9:16) video keeps everything that matters inside the safe zone, following Meta's Reels guidance (leave the top 14%, the bottom 35% and about 6% on each side clear): hooks, text, captions, graphics, Howie and the logo all sit between y 285 and 1240 and left of x 940. The bottom third is the "graveyard": the platform's caption and username cover it, so nothing important goes there (background and decoration only). The right corner (x > 940 from about y 700 down) is where the like, comment and share buttons sit. Never put graphics over a face in real footage. The engine's 916 layout (CFG in engine.py) does this automatically: logo at the top of the safe zone, content y 400-1035, Howie and burned-in captions just above the graveyard. `tools/qc.py` warns when text-like detail lands in those zones; treat it as a fix for anything made outside the engine (clips, talking-head polish, CapCut-style edits).

## Hook tests (A/B)
Michael's rule (Nov 14, 2026): test hooks with data. Run a test on HighLevel Weekly every other week (that task schedules its own posts through the queue, so it can split the accounts), and on any other video that a task schedules through `tools/queue/` (the hub's HighLevel button sends variant A to every account). For a test, add `"variants": {"b": {...}}` with a different opening: `head1`/`head2`/`sub2` on screen and `vo.intro` when voiced (for example a question vs a number vs a bold claim). The renderer outputs `v<size>-b.mp4` next to the A files. Posting: one variant goes to the Lewis Marketing brand accounts (Facebook page, Instagram @lewismarketingoc, Threads @lewismarketingoc, TikTok @michatin2yx, YouTube Lewis Marketing, LinkedIn page, Bluesky), the other to Michael's personal accounts (Instagram @therealmichaellewis, Threads, TikTok @michaellewisoc, YouTube @michaellewisoc, LinkedIn profile). Alternate which variant gets the brand accounts from one test to the next. Same captions apart from the first line, same time. Record it on the hub daily doc: `asset.hookTest = {a:{hook, type}, b:{hook, type}, brandGets:"a"|"b", started:<date>}` where type is question, number, bold claim, story, or how-to. The weekly social sync scores each test after 48 hours: each post's likes+comments*2+shares*3 divided by that account's average for the last 28 days, so the brand and personal audiences are compared fairly. It keeps the results in `dsconfig/settings.hookTests` and the winning hook types in `whatWorks`. Hooks stay true and paid off; no clickbait.

## Real footage: clips and talking-head videos
See `daily-social/clips/CLIPS.md` (uploads in HighLevel Media Storage > "Video recordings", automatic transcripts, branded clips from long recordings, polished phone videos).

## Look performance
The weekly social sync compares videos by look, format, Howie and voice (engagement per post from HighLevel insights, joined with each daily doc's `asset.style/format/howie/voice`) and keeps the scoreboard in `dsconfig/settings.videoLooks` and the weekly `insights` doc. Treat it as directional until a look has at least 4 videos.

## Voice (Michael's rule, Nov 21, 2026)
Every Lewis Marketing voiceover uses the male voice `lm_male` (Kokoro am_fenrir 80% + am_puck 20%, full-precision model) read the expressive way: unit by unit, a wider pitch melody, questions rise, statements settle, and natural pauses of a beat or two (longest after a question, a setup ending in a colon, or a short punchy line; a breath before the closing line). Write "vo" lines the way a person talks and star the one or two words a person would stress (`"vo": "Nobody picks up. So what do they *do*?"`); stars never show on screen, and numbers get stress automatically. Do not set "voiceName" unless Michael asks for a different voice. Details: voice.py.
