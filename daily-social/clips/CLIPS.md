# Clips from real footage (clip.py)

Michael's rules (Nov 14, 2026): cut long recordings into short clips automatically, and polish his phone videos (captions, name and title, text cards, end card). Behind the Storefront clips are marketing content only (see daily-social/SKILL.md). Clips do not need Howie (he may appear on the end card).

## How footage arrives
Michael (or the team) uploads video files to HighLevel Media Storage, folder **Video recordings** (id 6af8ca80893246071f817d87), in the Lewis Marketing sub-account. Name the file so it says what it is (for example `bts-ep2-flooring-design.mp4`, `marketing-lens-ep4.mp4`, `michael-reviews-tip.mov`).
The "Video recordings" GitHub Action (every two hours, 7 AM to 5 PM Central, or on demand) downloads each new file, transcribes it with word timings (Whisper small.en) and records it in `daily-social/clips/sources.json` with:
- `kind`: `talking` = portrait and under 5 minutes (a phone video to polish), `long` = everything else (a recording to cut into clips);
- `transcript`: `daily-social/clips/transcripts/<slug>.json` plus a readable `<slug>.txt` with timestamps;
- `status`: `transcribed` -> `planned` (specs written) -> `drafted` (hub drafts saved) or `skipped`.

## Long recordings -> clips (video-clips scheduled task)
1. Read the `.txt` transcript and pick the 3 to 6 strongest moments, 20 to 75 seconds each, that stand alone: a clear question and answer, a lesson, a story with a point. Behind the Storefront: marketing moments only (how the business wins and keeps customers, reaches people, reviews and word of mouth, follow-up, lessons for other owners); never the guest's industry advice on its own. Never use a moment that names a customer, shares private details, or that the guest would not want public.
2. For each moment write `daily-social/clip-specs/<slug>-c<n>.json`:
```json
{"source": "<sources.json url>", "transcript": "daily-social/clips/transcripts/<slug>.json",
 "keep": [[start, end]], "style": "navy|light|bold (rotate)", "eyebrow": "BEHIND THE STOREFRONT | THE MARKETING LENS",
 "title": "the hook, true to the clip, under 70 characters",
 "lowerThird": {"name": "Guest first name", "role": "Business, Town", "at": <output s when they first speak>},
 "cards": [{"at": <output s>, "dur": 3, "text": "the lesson in under 6 words"}],
 "endCard": {"cta": "...", "button": "Book a call: lewismarketingoc.com"}, "music": null,
 "out": "daily/clips/<slug>-c<n>"}
```
`keep` can hold several parts to cut out tangents (start each part at the beginning of a word and end it after the last word of a sentence; check the word timings in the JSON). You no longer need to cut "um"s and pauses by hand: `tighten` (on by default) does it, see below. `music` stays null on interviews unless the audio is quiet.
Two-person interviews filmed wide (both people in one 16:9 shot): use `"layout": "follow"` so the 9:16 crop cuts to whoever is talking, instead of the branded frame.
3. Push the specs; the "Render videos" Action renders `v916.mp4` (branded 9:16 frame: hook on top, footage in the middle, big captions under it) and `v169.mp4` (footage with captions and lower third) plus covers and `captions.srt`, and writes `tools/render/results/<slug>-c<n>.json`.

## Phone videos -> polished (video-clips scheduled task)
Spec in `daily-social/clip-specs/<slug>.json` with `layout` "full" (portrait), `keep` that drops false starts and repeated takes (tighten handles the "um"s and pauses), `title` (the hook, shown for the first 3 seconds; leave out if Michael's first sentence is already the hook), `lowerThird` {"name": "Michael Lewis", "role": "Owner, Lewis Marketing"}, 1 to 3 `cards` on the key points, `endCard`, and `music` 0-3 (quiet bed) unless he asked for none. Output: `v916.mp4` (plus `v45.mp4` if a feed version is wanted: add "45" to `sizes`).

## Automatic polish (Michael's request, Nov 14, 2026)
These run on every clip unless the spec turns them off. `clip-report.json` in the output folder says what each one did; mention it in the draft note ("tightened 4.2 s, 2 pop-ups").
- **Tighten** (`"tighten": true` default; `{"maxPause": 0.6}` for a calmer pace; `false` to skip): removes "um", "uh", "er", "hmm", stutters ("the the") and pauses longer than 0.45 s, with soft audio joins. Card, lower-third and pop-up times move with the edit. Transcripts made since Nov 14 keep the fillers so they can be found; older transcripts still get the pause and stutter cuts.
- **Follow the speaker** (`"layout": "follow"`, or `"layout": "full"` on 16:9 footage; `"cropX": 0-1` pins the crop instead): finds the faces, watches whose mouth moves while there is sound, and cuts the 9:16 crop to that person (holds each shot at least 1.5 s so it never flickers).
- **Pop-up visuals** (`"popups": "auto"` default): when a topic is mentioned a small icon card pops in for 2.6 s: Reviews, Your website, CRM and automation, Text back, Email, Found on Google, Advertising, Social media, AI tools, Phone calls, Online booking. At most 4 per clip, 6 s apart, never over a text card, the lower third, the hook or the end. Place them yourself with `[{"at": <output s>, "kind": "reviews", "label": "Google reviews"}]`, or `false` for none. The icons are drawn shapes, never other companies' logos.
- **Safe zones**: on 9:16 the captions sit left of the like and comment buttons and above the bottom caption area; the lower third stays above y 1540; the logo bug sits below the top bar.
- **YouTube thumbnails** (`"thumbnail"` in the spec, required for any clip that goes to YouTube as a regular video and for The Marketing Lens episodes): `thumb.py` picks the sharpest frames with a clear face and open eyes and builds `thumb-a.jpg` (navy) and `thumb-b.jpg` (brand blue, all-white logo), 1280x720. Behind the Storefront thumbnails always use the duo layout (Michael's rule, Nov 14, 2026): Michael on the left, the guest on the right, the hook in the centre and "with <guest>, <business>" under it. Set `"guest": "Denise, Jorgensen Hearing Center"` in `thumbnail` (otherwise it comes from the lower third). The whole recording is searched for both faces and Michael is recognised from `daily-social/clips/ref/michael-*.jpg` (add a new photo of him there if he changes his look); if a thumbnail shows the wrong person on a side, pin frames with `"michael": [source s]` and `"guestFrames": [source s]`. Give A and B different hook text (3 to 6 words, one highlighted phrase) so the test teaches something. After the video is live, upload both in YouTube Studio > the video > Thumbnail > Test & compare (YouTube picks the winner by watch time); record the winner in the hub daily doc `asset.thumbTest = {a, b, winner}`.
- **Quality check**: the render Action runs `tools/qc.py` on every output; `ok` is false when it finds an error (wrong size or codec, too quiet or loud, opens on black, over 180 s for 9:16). Read `qc.warnings` too and fix anything real before drafting.

## Drafts
Each finished clip becomes a hub daily doc (status "review", series "Clips" or "Behind the Storefront" or "Michael on camera") on an open slot within the next 14 days, with copy for facebook, instagram, threads, linkedin, bluesky, tiktok (and youtube title for Shorts), firstComment, alt, and `asset: {type:"video", file:<raw v916>, poster:<raw cover916>, note:"16:9: <raw v169>", clip:true, spec:<spec path>, specData:<spec>, thumbs:[<raw thumb-a>, <raw thumb-b>] when made}`. Run `python3 tools/qc.py copy posts.json` on the copy before saving the draft and fix every error. Michael approves before anything is scheduled.

## Local use
`python3 daily-social/clips/clip.py transcribe <file or URL> out.json` (container: falls back to the tiny model on the models branch), `python3 daily-social/clips/clip.py render spec.json OUTDIR`. Rendering a 60-second clip takes about a minute per size.

## 9:16 safe zone (Michael's rule, Nov 25, 2026)
Keep the speaker centered and every hook, caption, lower third, card, pop-up and logo inside the safe zone (Meta's Reels guidance: leave the top 14%, the bottom 35% and about 6% each side clear). The bottom third is the "graveyard" where the platform's caption and username sit, and the right corner from about y 700 down holds the like, comment and share buttons. Never put graphics over a face; graphics support the person, they don't replace them. clip.py's 9:16 layouts do this automatically (logo at the top of the safe zone, captions just above the graveyard, pop-ups clear of the buttons); qc.py flags anything that lands in those zones.

