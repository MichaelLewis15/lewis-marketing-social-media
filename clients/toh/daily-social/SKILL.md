---
name: daily-social-toh
description: Run Touch of Hope's daily-social automation - write one faith-filled post per empty day, 7 days ahead, for Facebook, Instagram and Google Business, saved to the Touch of Hope calendar for review (or scheduled in Touch of Hope's HighLevel sub-account when autopilot is on).
---

# daily-social for Touch of Hope (this client only)

One post per day for **Touch of Hope** (Christian book and gift store, 915 3rd Ave, Sheldon, Iowa; owner Julie Heerde), on days that have nothing else on the calendar or in HighLevel, always covering the next 7 days. Mon-Sat posts go out at **10:00 AM**, Sunday posts at **7:00 AM** (America/Chicago). Never touch any other client or sub-account.

## Fixed facts
- HighLevel connector: `HighLevel - Lewis Marketing` (search_operations / describe_operation / execute_operation).
- Sub-account: **Touch of Hope**, location ID **`rQUaY51pwEHLCOv6qlQL`** (company `seQi31bh8TKgcHvMgYIx`, user `9NPcOb0IKVBMR7h4oRT0` = Julie). Every run first calls `get-location` and stops (log + notify) unless the name contains "Touch of Hope".
- Calendar artifact (settings, posts, logs): https://claude.ai/artifact/NtjURm31gAWoX488hjyNXa
  - `dsconfig/settings`: autopilot flag, accounts, links, dossier, hours, audience, voice, pillars, format, hashtags, platformRules, translations, recentTopics, recentVerses, calendarDates, quietDates, media.
  - `daily/ds-YYYY-MM-DD`: one doc per daily post (the calendar shows these as posts).
  - `hl/pds-YYYY-MM-DD`: HighLevel post IDs per channel `{_id:"ds-YYYY-MM-DD", <channel>:{postId, sig:"auto:YYYY-MM-DD", at, when, loc}}` (same format the calendar's Schedule button writes).
  - `dslog/YYYY-MM-DD-HHMM`: run log `{at, mode, summary, created[], scheduled[], skipped[], flags[]}`.
  - `posts/p<id>`: saved edits to calendar posts (a `date` there moves a post).
- Media repo: `MichaelLewis15/lewis-marketing-social-media` (public, GitHub Pages). Daily images go in `clients/toh/daily/<date>.png` and `clients/toh/daily/gbp/<date>.png`; public URL base `https://michaellewis15.github.io/lewis-marketing-social-media/clients/toh/`. Engine: `clients/toh/daily-social/engine/render_toh.py` (spec format in its docstring). Commit as `Claude <noreply@anthropic.com>`; `git fetch origin main && git rebase origin/main` before pushing.

## Each run
1. **Settings.** Read `dsconfig/settings` (ArtifactData get). Confirm the location (above).
2. **Window.** Tomorrow through today + 7 days, Chicago time.
3. **Busy days.** A day is taken if any of these has something on it:
   - HighLevel `get-posts` for the location (POST body `{type:"all", skip:"0", limit:"100", fromDate, toDate}`; page with skip; save the response to a file and parse it with code).
   - `settings.calendarDates`, plus the calendar's `posts` collection (a saved `date` moves a post onto that day and off its old one), and the `daily` collection (any status except "skipped" counts; a "skipped" doc means Julie or Michael turned that day down, so leave it empty).
   Also skip `settings.quietDates` (log them as skipped). Never put two daily posts on one day. If a daily doc already exists for a date, leave it alone.
4. **Pillar and topic per empty day.** Pillars and their shares are in `settings.pillars` (Daily Verse, Gift idea, In the store, Conversation starter). Sundays are always Daily Verse (store closed: no shopping, hours or "stop in" language; GBP button none). Balance pillars across the window and against the calendar posts around each day (don't put two gift posts on back-to-back days). Use the calendar and the season: upcoming holidays and church seasons (All Saints, Thanksgiving, Advent, Christmas, Epiphany, Lent, Easter), occasions people shop for (birthdays, sympathy, new baby, baptism, confirmation, graduation, weddings, Mother's and Father's Day, pastor and teacher appreciation). Never repeat a topic in `recentTopics` from the last 60 days.
5. **Verse.** Every post has one verse, quoted exactly. Rotate `settings.translations` (KJV, NKJV, NIV, NLT, ESV) so no two posts in a row (counting calendar posts) share a translation. Never reuse a verse in `recentVerses` within 90 days. VERIFY the exact wording with WebFetch on `https://www.biblegateway.com/passage/?search=<reference>&version=<KJV|NKJV|NIV|NLT|ESV>`. If it can't be verified, switch to KJV wording you can confirm and flag it. Keep quotations short (one or two verses).
6. **Copy** (voice, format, hashtags and platformRules in settings; no emojis anywhere in captions, first comments or alt text; never invent sales, prices, events or products in stock; no statistics):
   - facebook: hook line, 2-5 short lines or a short bullet list (•), the verse as `"<text>" <Reference> (<TRANSLATION>)`, one closing line, 3 hashtags. If there's a link, it goes ONLY in the first comment.
   - instagram: shorter version, "link in our bio" if a link fits, then the hashtag block from settings.
   - gbp: first line `UPDATE POST · Button: Call now` or `UPDATE POST · Button: Learn more → <saved link>` (Sundays: `UPDATE POST · Button: none`), blank line, then 2-3 sentences (max 1,500 characters), no links, phone numbers or emails, mentions Sheldon and what the store carries.
   - firstComment: one friendly sentence (plus the exact saved link when the post has one). alt: describe the graphic and its words.
   - Links are copied exactly from `settings.links`. Never invent or edit a URL.
7. **Image.** Write a spec for `render_toh.py` (layout verse | list | question; eyebrow; a 4-7 word headline with one `<em>` accent; items for list posts (3-5, under ~32 characters, no emojis); the same verse; one art key that fits; optional pill such as "Free gift wrapping"; bg cream | sage | dawn; Sundays use `footRight: "Open Mon–Sat · <b>Sheldon, Iowa</b><br>touchofhopesheldon.com"`). Run `python3 clients/toh/daily-social/engine/render_toh.py spec.json clients/toh/daily` inside the repo clone (needs `pip install playwright pillow`; Chromium is at /opt/pw-browsers). The report must say `"ok": true`; then LOOK at both PNGs (Read the image) and fix anything cramped, cut off or overlapping. Commit `clients/toh/daily/<date>.png`, `clients/toh/daily/gbp/<date>.png` and the spec (`clients/toh/daily-social/specs/<date>.json`), push, and wait until the public URL returns the image (WebFetch or a HEAD request; GitHub Pages takes about a minute).
8. **Save** `daily/ds-<date>` with: id "ds-<date>", date, day ("Tue, Nov 3"), time (postTime, or sundayTime on Sundays), pillar "Daily Social · <pillar label>", series "Daily Social", topic (slug), title, goal, verse ("Psalm 46:10 · KJV"), linkKey (or null), ctaLink (or null), hashtags, asset `{type:"graphic", file:"<public URL of the 4:5 PNG>", gbp:"<public URL of the 4:3 PNG>", note:"4:5 graphic made by daily-social"}`, alt, firstComment, copy{facebook, instagram, gbp}, status, createdBy "daily-social", createdAt (ISO).
9. **Schedule (only when `settings.autopilot` is true).** One `create-post` per channel (never a mixed request). Body:
   `{accountIds:[<settings.accounts[ch]>], summary, media:[{url, type:"image/png", altText}], status:"scheduled", scheduleDate:<post time in Chicago as ISO UTC; CST from Nov 1, 2026 = UTC-6, CDT = UTC-5>, type:"post", userId, createdBy:userId}`
   plus `facebookPostDetails:{type:"post"}` and `followUpComment:<firstComment>` for facebook, `instagramPostDetails:{type:"post"}` and `followUpComment` for instagram, and for gbp `gmbPostDetails:{gmbEventType:"STANDARD", actionType:"call"|"learn_more"|"none", url:<link for learn_more>}` with the text after the setup line and the 4:3 image.
   Tracking: add `utm_source=<facebook|instagram|google>&utm_medium=<social|organic for google>&utm_campaign=daily-social` to touchofhopesheldon.com links in captions, and `utm_source=social&utm_medium=comment&utm_campaign=daily-social` in first comments.
   idempotencyKey `toh-ds-<date>-<channel>`. The post ID is at `data.results.post._id`. Record each in `hl/pds-<date>`, then set the daily doc `status:"scheduled"`. Spot-check one with `get-post`.
   When autopilot is false: leave `status:"review"` and don't touch HighLevel. Julie or the Lewis Marketing team approves on the calendar (edit, Save changes, then the post's "Schedule in HighLevel" button), or Michael tells Claude "go" (then set `autopilot:true` and schedule every `review` post).
10. **Log** to `dslog`: what was created or scheduled and for which day, what was skipped and why, flags. Append the new topics (with dates) to `recentTopics` and the verses to `recentVerses` (pin if_version).
11. **Notify** Michael with a short summary (the run's final reply is sent as a push notification): days filled, pillar and verse for each, anything skipped or needing him.

## Guardrails
- Social posts only. Never DM, text or email anyone.
- Touch of Hope only: never write to any other calendar or sub-account. Never edit or delete existing calendar posts or their HighLevel posts.
- If data is missing or a step fails (connector down, render error, push refused, Pages not serving the image, verse can't be verified), skip that item, log it and flag it. Don't guess.
- If an action isn't available through the connector, leave the post in review and give Michael the 2-minute manual step (Social Planner > New Post > paste caption, upload the image from its URL, schedule, add the first comment).
