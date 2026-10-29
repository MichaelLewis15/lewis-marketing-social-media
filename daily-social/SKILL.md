---
name: daily-social
description: Run Lewis Marketing's daily-social automation - write and schedule one educational post per empty day, 7 days ahead, in the Lewis Marketing HighLevel Social Planner, tracked in the Lewis Marketing social hub.
---

# daily-social (Lewis Marketing only)

One educational post per day for **Lewis Marketing only** (never a client account), on days that have nothing else scheduled, always covering the next 7 days, at **7:30 AM America/Chicago**.

## Fixed facts
- HighLevel connector: `HighLevel - Lewis Marketing` (search_operations / describe_operation / execute_operation).
- Sub-account: **Lewis Marketing**, location ID **`Auzaxxusb4MezZd78QIC`** (company `seQi31bh8TKgcHvMgYIx`, user `0T5YzQFGjmXmN5py288b`). Every run first calls `get-location` and stops (log + notify) unless the name trims to "Lewis Marketing".
- Hub artifact (settings, posts, logs): https://claude.ai/artifact/YLBNhbEhrs7SEkAX7sJ9yi
  - `dsconfig/settings`: autopilot flag, account IDs, saved links, dossier, ICP, voice, platform rules, recentTopics, calendarDates, quietDates.
  - `daily/<ds-YYYY-MM-DD>`: one doc per daily post (the hub renders these).
  - `hl/p<ds-YYYY-MM-DD>`: HighLevel post IDs per channel `{_id, <channel>:{postId, sig:"auto:<date>", at, when}}`.
  - `dslog/<YYYY-MM-DD-HHMM>`: run log `{at, mode, summary, created[], scheduled[], skipped[], flags[]}`.
- Media repo: `MichaelLewis15/lewis-marketing-social-media` (public). Raw URL base `https://raw.githubusercontent.com/MichaelLewis15/lewis-marketing-social-media/main/`. Graphic engine: `daily-social/engine/render_daily.py` (spec format in its docstring). Commit as `Claude <noreply@anthropic.com>`; `git fetch origin main && git rebase origin/main` before pushing.

## Each run
1. **Settings.** Read `dsconfig/settings` (ArtifactData get). Confirm the location (above).
2. **Window.** Tomorrow through today + 7 days, Chicago time.
3. **Busy days.** A day is taken if any of these has something on it:
   - HighLevel `get-posts` (POST body `{type:"all", skip:"0", limit:"100", fromDate, toDate}`; page with skip; the response is large, so save it and parse with code).
   - `settings.calendarDates`, the hub collections `daily`, `posts` (LEWIS-OS) and `edits` (an edit's `date` moves a post).
   Also skip `settings.quietDates` and LEWIS-OS closures (artifact https://claude.ai/artifact/E3pGawMbWLNG42qs1PqNfY, `settings/main.closures`). Never put two daily-social posts on one day. If a daily doc already exists for a date, leave it alone.
4. **Topic per empty day.** Educational ("Teach"). One specific problem a small-business owner in the ICP has. Never repeat a topic in `recentTopics` from the last 60 days, or one already on the calendar in the window. Sources, in order: the dossier and ICP in settings, the Drive sheet "October Content Ideas" (and newer content-ideas sheets), the latest Lewis Marketing blog posts (lewismarketingoc.com is not reachable from the cloud sandbox; try WebSearch, and if it fails, flag it), the links directory, and what is already in the Social Planner. Vary the service area (websites, SEO, Google Ads, Meta Ads, CRM/automation, email, content, analytics, reviews/local).
5. **Copy** (brand voice in settings; no emojis anywhere in captions, first comments or alt text; no invented stats; any statistic needs a credible source link; never shorten "Piper Financial Group"):
   - Hook line on the problem (under 12 words; a question or number), a simple numbered how-to (3-5 steps), one short paragraph on how Lewis Marketing helps, then 2-3 hashtags.
   - The CTA link is copied exactly from `settings.links`. Never invent or edit a URL. If no saved link fits, use `website` and flag it.
   - Platform versions: facebook (link only in the first comment), instagram (says the link is in the first comment), threads (max 500 chars), linkedin (longer, professional), bluesky (max 300 chars), gbp (first line `UPDATE POST · Button: Book → <link>` or `Learn more → <link>`, blank line, then text with no links, phone numbers or emails; max 1500).
   - `firstComment`: one sentence plus the exact saved link. Also write `alt` (describe the graphic, mention Howie if he is in it) and a short `storyTip`.
6. **Image.** First search the HighLevel media library (`fetch-media-content`, query `{altType:"location", altId:<loc>, type:"file", limit:"50", query:"<keyword>"}`) for a branded Lewis Marketing graphic that clearly fits the topic; use its CDN URL if one does (GBP still needs a 4:3 version, so render one if the library image is not 4:3). Otherwise render one with the engine: write a spec JSON, run `python3 daily-social/engine/render_daily.py spec.json .` inside the repo clone (needs Pillow + numpy), look at the PNG, fix any overlap, commit `daily/<date>.png` and `daily/gbp/<date>.png`, push. Put **Howie** (poses idle, pointL, pointR, wave, cheer; default `{"pose":"pointL","x":985,"feet":1112,"h":215}`) in every graphic, never covering text. To add him to an existing image or reel, use `daily-social/howie-tools/place_howie.py` and `howie_reel.py`. Any video made must follow the lewis-marketing-video skill (Howie always in videos).
7. **Save** `daily/ds-<date>` with: id, date, day ("Sat, Oct 31"), time "7:30 AM", pillar "Daily Social · Teach", series "Daily Social", topic (slug), title, goal, linkKey, ctaLink, hashtags, asset `{type:"graphic", file:<full image URL>, gbp:<full 4:3 URL>, note}`, alt, firstComment, storyTip, copy{facebook, instagram, threads, linkedin, bluesky, gbp}, status, createdBy "daily-social", createdAt.
8. **Schedule (only when `settings.autopilot` is true).** One `create-post` per channel (never one mixed request; it trims copy to the strictest limit). Body:
   `{accountIds:[<settings.accounts[ch]>], summary, media:[{url, type:"image/png", altText}], status:"scheduled", scheduleDate:<7:30 AM Chicago as ISO UTC; CDT = 12:30Z, CST (from Nov 1, 2026) = 13:30Z>, type:"post", userId, createdBy:userId, followUpComment:<firstComment, all channels except gbp>}`
   plus `facebookPostDetails:{type:"post"}`, `instagramPostDetails:{type:"post"}`, and for gbp `gmbPostDetails:{gmbEventType:"STANDARD", actionType:"book"|"learn_more", url:<link>}` with the gbp text after the setup line and the 4:3 image. LinkedIn takes both account IDs in one request.
   Tracking: add `utm_source=<facebook|instagram|threads|linkedin|bluesky|google>&utm_medium=<social|organic for google>&utm_campaign=daily-social` to lewismarketingoc.com links in captions, and `utm_source=social&utm_medium=comment&utm_campaign=daily-social` in first comments, unless that would break a character limit.
   idempotencyKey `ds-<date>-<channel>`. The post ID is at `data.results.post._id`. Record each in `hl/pds-<date>` with `sig:"auto:<date>"`, then set the daily doc `status:"scheduled"`. Spot-check one with `get-post`.
   When autopilot is false: leave `status:"review"` and do not touch HighLevel; Michael approves in the hub (its HighLevel button schedules) or by telling Claude "go" (then set `autopilot:true` and schedule every `review` post).
9. **Log** to `dslog`: what was created or scheduled and for which day, what was skipped and why, and flags. Append the new topics with dates to `recentTopics`.
10. **Notify** Michael with a short summary (SendUserMessage, or the push notification when unattended): days filled, topics, anything skipped or needing him.

## Guardrails
- Social posts only. Never DM, text or email contacts. If messaging is ever added: never contact anyone unsubscribed, on Do Not Disturb or without consent, and keep daily sending low to protect the domain.
- If data is missing or a step fails (connector down, render error, push refused, unclear location), skip that item, log it and flag it. Do not guess.
- If an action isn't available through the connector, use the next best route (the hub's HighLevel button, or a ready-to-paste post) and give Michael the 2-minute manual step, e.g. "Social Planner > New Post > paste caption, upload image from <URL>, schedule Sat 7:30 AM, add the first comment".
- Never change client calendars or other sub-accounts.
