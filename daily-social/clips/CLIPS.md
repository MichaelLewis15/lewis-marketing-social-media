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
`keep` can hold several parts to cut out tangents or "um" stretches (start each part at the beginning of a word and end it after the last word of a sentence; check the word timings in the JSON). `music` stays null on interviews unless the audio is quiet.
3. Push the specs; the "Render videos" Action renders `v916.mp4` (branded 9:16 frame: hook on top, footage in the middle, big captions under it) and `v169.mp4` (footage with captions and lower third) plus covers and `captions.srt`, and writes `tools/render/results/<slug>-c<n>.json`.

## Phone videos -> polished (video-clips scheduled task)
Spec in `daily-social/clip-specs/<slug>.json` with `layout` "full" (portrait), `keep` that drops false starts, repeated takes and pauses over 0.7 seconds (use the word timings), `title` (the hook, shown for the first 3 seconds; leave out if Michael's first sentence is already the hook), `lowerThird` {"name": "Michael Lewis", "role": "Owner, Lewis Marketing"}, 1 to 3 `cards` on the key points, `endCard`, and `music` 0-3 (quiet bed) unless he asked for none. Output: `v916.mp4` (plus `v45.mp4` if a feed version is wanted: add "45" to `sizes`).

## Drafts
Each finished clip becomes a hub daily doc (status "review", series "Clips" or "Behind the Storefront" or "Michael on camera") on an open slot within the next 14 days, with copy for facebook, instagram, threads, linkedin, bluesky, tiktok (and youtube title for Shorts), firstComment, alt, and `asset: {type:"video", file:<raw v916>, poster:<raw cover916>, note:"16:9: <raw v169>", clip:true, spec:<spec path>, specData:<spec>}`. Michael approves before anything is scheduled.

## Local use
`python3 daily-social/clips/clip.py transcribe <file or URL> out.json` (container: falls back to the tiny model on the models branch), `python3 daily-social/clips/clip.py render spec.json OUTDIR`. Rendering a 60-second clip takes about a minute per size.
