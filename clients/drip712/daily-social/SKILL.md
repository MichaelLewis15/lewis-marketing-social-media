---
name: daily-social-drip712
description: Run Drip712's daily-social automation in gap-only mode - keep Drip 712 near nine evenly spaced posts a month by drafting a replacement only when a gap opens, saved to the Drip712 calendar for approval.
---

# daily-social for Drip712 (this client only)

**Drip 712** (drip712.com) is an IV hydration, injection and wellness med spa at 101 Runger Ave N, Suite G, Sheldon, Iowa. Contact: call or text 712-403-2036 (texting is quickest), drip712ivmedspa@gmail.com. Hours by appointment: Mon, Tue, Thu, Fri 9-5; Wed 9-7; Sat and Sun 9-12. House visits in the Sheldon area ($50 fee, waived for groups of 4+). HSA/FSA, cash, card, Venmo, Apple Pay; no insurance billing. Age minimum 13 and 100 lb with an adult present for minors. Tagline: "Wellness from within." Never touch any other client or sub-account.

## Cadence (Michael's rule)
Drip 712 posts **about nine times a month, spread evenly** (roughly every 3-4 days). This is NOT one post a day. Daily Social only fills a gap: a post is drafted for a day only when the 4 days ending that day and the 3 days after it have nothing planned (calendar posts, daily docs that are not "skipped", or HighLevel posts), AND the month's count (planned + daily, excluding skipped) is under 9 for that calendar month. Never two posts within 2 days of each other. Default post time 7:30 AM America/Chicago (reels 6:30 PM).

## Fixed facts
- HighLevel connector: `HighLevel - Lewis Marketing` (search_operations / describe_operation / execute_operation).
- Sub-account: **Drip712**, location ID **`SwSQVDI5Lol5wzk5D0H1`**, user `LcrbkUvKzy6WCOWNxvxm` (Kymlee Klynsma). Every run first calls `get-location` and stops (log + notify) unless the name contains "Drip712".
- Accounts: Facebook `6abbf5b5430a9dadbaad2cb7_SwSQVDI5Lol5wzk5D0H1_1013044135217870_page`, Instagram `6abbf6177d75f87dc2c024eb_SwSQVDI5Lol5wzk5D0H1_17841480192331543`, Google Business `6abbf5ea34fd765641d198cc_SwSQVDI5Lol5wzk5D0H1_4372459283784543543`.
- Calendar artifact: see `CALENDAR_URL` in `dsconfig/settings.calendarUrl` (ArtifactData). Collections: `dsconfig/settings`, `daily/ds-YYYY-MM-DD`, `posts/p<id>` (saved edits; a `date` moves a post), `hl/p<id>`, `approvals/p<id>`, `hlqueue`, `dslog`, `news`, `questions`, `insights`, `growth`, `native`.
- Media repo: `MichaelLewis15/lewis-marketing-social-media`, folder `clients/drip712/`. Public base `https://michaellewis15.github.io/lewis-marketing-social-media/clients/drip712/`. Daily images: `clients/drip712/daily/<date>.png` and `clients/drip712/daily/gbp/<date>.png`. Engine: `clients/drip712/daily-social/engine/render_drip.py` (spec format in its docstring; layouts list, stat, question, myth, greeting). Reels: `engine/reel_drip.py`. Commit as `Claude <noreply@anthropic.com>`; `git fetch origin main && git rebase origin/main` before pushing.

## Content rules
- Pillars and target mix: Teach 45% (drip and service explainers, prep tips, myths, FAQs), Promote 25% (services, house parties, bundles), Personal 15% (team, holidays, office), Engage 15% (this-or-that, fill in the blank, polls). Pillar field is exactly "Teach", "Engage", "Promote" or "Personal" (daily docs: "Daily Social · Teach" etc.).
- Health and FTC rules: describe ingredients and why people choose a service ("a popular choice for...", "people ask us about it for..."). Never say a drip or injection treats, cures, prevents or protects against any disease (no COVID, flu-prevention, cancer, diabetes or weight-loss guarantees). Never claim "clinically proven". Immune posts must say drips are not a substitute for vaccination or medical care. Rx items (GLP-1, Botox, filler, PRP) are mentioned only as "consults with our medical director" and only when the team has confirmed them.
- Never invent prices, specials, credentials, staff names or events. Known prices only: NAD+ 100 mg take-home injections 10 for $300; NAD+ 400 mg patches 6 packs for $200. Anything unknown goes in [brackets] with a `pending` note.
- Statistics: only from credible sources (CDC, NIH/NIDDK/ODS, peer-reviewed journals), printed as a source line on the graphic and linked in the first comment. No statistic is better than an unsourced one.
- No emojis anywhere in captions, first comments or alt text. Michael's hook rule: every post opens with a hook; a double hook only where it fits (about 1 in 3).
- Copy shape: facebook (hook, 3-6 short lines or • bullets, a closing question or CTA, 3 hashtags: #Drip712 #SheldonIowa + one topical); instagram (shorter, "link in our bio", then `#Drip712 #SheldonIowa #IVTherapy #IVHydration #WellnessFromWithin #NWIowa #MedSpa` plus 1-2 topical); gbp (first line `UPDATE POST · Button: Book → https://www.drip712.com/book-online` or `Learn more → <saved link>` or `Call now` or `none`, blank line, 2-4 sentences under 1,500 characters mentioning Sheldon, no emojis). firstComment: one friendly line plus the exact saved link or source link. alt: describe the graphic and its words.
- Saved links (copy exactly): https://www.drip712.com, /services, /nadtherapy, /pelvicfloortherapy, /faq, /contact, /book-online.

## Each run
1. Read `dsconfig/settings`; confirm the location.
2. Window: tomorrow through today + 7 days, Chicago time.
3. Busy days: HighLevel `get-posts` (POST body `{type:"all", skip:"0", limit:"100", fromDate, toDate}`, needs an idempotencyKey; save to a file and parse with code), the calendar's posts (with moved dates from `posts/p<id>`), and the `daily` collection.
4. Apply the cadence rule above. Most runs should create nothing; that is correct.
5. For each gap day: choose pillar and topic (season, holidays, `ideaQueue`, `news` and `questions` items first; never a topic used in the last 60 days per `recentTopics`).
6. Render the graphic with `render_drip.py` (look at both PNGs; fix anything cramped), commit and push, wait for the public URL to serve.
7. Save `daily/ds-<date>` (id, date, day, time, pillar "Daily Social · <pillar>", series "Daily Social", topic, title, goal, asset {type:"graphic", file, gbp, note}, alt, firstComment, copy{facebook, instagram, gbp}, status "review", createdBy "daily-social", createdAt).
8. NEVER schedule in HighLevel from this task. Every post is approved on the calendar by someone with access, then scheduled from the calendar (or by the send queue).
9. Log to `dslog` and append topics to `recentTopics`. Notify Michael only when something was created or needs him.

## Guardrails
Social posts only. Never DM, text or email anyone. Drip712 only. Never edit or delete existing calendar posts or HighLevel posts. If a step fails, skip, log and flag it; don't guess.
