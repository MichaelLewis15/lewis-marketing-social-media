# HighLevel Weekly (Fridays, 2:30 PM Central)

Michael's rule (Nov 9, 2026): every Friday at about 2:30 PM Central, Lewis Marketing posts a recap of the HighLevel releases that went out that week.
- A graphic for platforms that do not take video (Google Business Profile).
- A 16:9 video for platforms that take landscape video (YouTube, LinkedIn, Bluesky).
- A 9:16 video for the rest (Instagram Reels, Facebook Reels, Threads, TikTok).
Howie is in every graphic and video (the renderer handles this). It is the Friday afternoon post: when the daily-social or monthly-planner tasks fill slots, Friday's afternoon slot belongs to HighLevel Weekly.

## 1. Research (Monday to Friday of this week)
- Primary source: the HighLevel changelog, https://highlevel.canny.io/changelog (fetch it; open individual entries when a summary is unclear). Use only entries dated Monday through Friday of this week, Central time.
- Pick the 3 to 5 releases that matter most to Lewis Marketing's audience (small and local businesses, service businesses, agencies): things that win leads, save time, or help them get paid. Skip pure bug fixes, time zone tweaks and developer-only API changes unless nothing else shipped.
- If fewer than 3 meaningful releases shipped, use 3 anyway by including the best smaller ones; if fewer than 3 exist at all, skip the week and say so in the run log.
- Never invent a feature, availability or price. Say "beta" when the changelog says beta. Mark the source for each item.

## 2. Spec and render
Write `daily-social/hl-weekly/specs/<Friday YYYY-MM-DD>.json`:
```json
{"week": "Nov 9-13, 2026", "music": 0,
 "items": [{"title": "short benefit-led title, under 60 characters", "why": "one plain sentence on why a business owner should care, under 140 characters", "tag": "New|Beta|Update"}],
 "cta": "Want these set up in your account?"}
```
Rotate `music` 0 to 3 week to week. Then:
```
cd daily-social/hl-weekly && TMPDIR=/tmp python3 render_weekly.py specs/<date>.json ../../daily/hl-weekly/<date>
```
Outputs: `v916.mp4`, `v169.mp4`, `gbp.png`, `cover916.jpg`, `cover169.jpg`. Look at a frame sheet of both videos and the PNG before posting (no text cut off, nothing behind Howie).

## 3. Copy (no emojis anywhere; statistics only with a credible source link)
- Hook on line one (a double hook on roughly one in three weeks, never on consecutive days). Example hooks: "HighLevel shipped 5 updates this week. Here are the ones worth your time." / "Your HighLevel account got better this week."
- facebook (reel): hook, the releases as short numbered lines, CTA to book a call; link goes in the first comment.
- instagram (reel): same, 3 to 5 hashtags (#HighLevel #GoHighLevel #MarketingAutomation #SmallBusinessTips #NWIowa).
- threads (video): under 500 characters.
- linkedin (16:9): Michael's first person, 120 to 220 words, why these matter for a business owner, CTA, link in the first comment.
- bluesky (16:9): under 300 characters; first comment also under 300 characters.
- youtube (16:9, regular video, not a Short): title "What's New in HighLevel: <week>" (under 70 characters); description = linkedin-style summary plus the changelog link and https://lewismarketingoc.com.
- tiktok (9:16): instagram copy.
- gbp (graphic): "UPDATE POST · Button: Learn more -> https://lewismarketingoc.com" style setup line, then 2 to 4 sentences, no phone numbers.
- firstComment: "This week's HighLevel release notes: https://highlevel.canny.io/changelog  Want help setting any of these up? https://lewismarketingoc.com" (UTM-tag lewismarketingoc.com links with utm_campaign=highlevel-weekly).
- alt: describe Howie and the 3 to 5 release titles.

## 4. Schedule (2:30 PM Central that Friday, every channel)
Write `tools/queue/hl-weekly-<date>.json` = {"name": "hl-weekly-<date>", "requests": [...]}, one request per channel group, each a full create-post body with `status: "scheduled"`, `scheduleDate` = Friday 2:30 PM Central in UTC (20:30Z in CST, 19:30Z in CDT), `userId`/`createdBy` 0T5YzQFGjmXmN5py288b, media from raw GitHub URLs of the files above:
| key ch | accounts | media | extras |
|---|---|---|---|
| facebook | Facebook page | v916.mp4 | type "reel", facebookPostDetails {type:"reel"}, followUpComment |
| instagram | both Instagram accounts | v916.mp4 | type "reel", instagramPostDetails {type:"reel", showOnFeed:true}, followUpComment |
| threads | both Threads profiles | v916.mp4 | followUpComment |
| linkedin | LinkedIn page + profile | v169.mp4 | followUpComment |
| bluesky | Bluesky | v169.mp4 | followUpComment (300 max) |
| youtube | both YouTube channels | v169.mp4 | youtubePostDetails {title, privacyLevel:"public", type:"video"} |
| tiktok | both TikTok accounts | v916.mp4 | tiktokPostDetails {privacyLevel:"PUBLIC_TO_EVERYONE", enableComment:true, enableDuet:false, enableStitch:false, videoDisclosure:false, promoteOtherBrand:false, promoteYourBrand:false} |
| gbp | Google Business | gbp.png | gmbPostDetails {gmbEventType:"STANDARD", actionType:"learn_more", url} |
Account ids are in `tools/hl_create.py` (ALLOWED). Commit the renders, spec and queue file in one push. The "HighLevel post queue" GitHub Action creates the posts (never twice), hosts the TikTok video in HighLevel's "TikTok videos" folder, and commits `tools/queue/results/hl-weekly-<date>.json`. Pull and check every request has a postId.

## 5. Hub
Hub artifact https://claude.ai/artifact/YLBNhbEhrs7SEkAX7sJ9yi (ArtifactData):
- daily doc `hlw-<date>`: {id, date, day, time:"2:30 PM", title:"HighLevel Weekly: <week>", series:"HighLevel Weekly", pillar:"Teach", status:"scheduled", createdBy:"highlevel-weekly", asset:{type:"video", file:<raw url v916.mp4>, poster:<raw url cover916.jpg>, gbp:<raw url gbp.png>, note:"16:9 version for YouTube, LinkedIn, Bluesky: <raw url v169.mp4>"}, copy:{facebook, instagram, threads, linkedin, bluesky, gbp, tiktok}, firstComment, alt, sources:[changelog entry urls]}
- hl doc `phlw-<date>`: {_id:"hlw-<date>", <ch>:{postId, sig:"auto:<date>", at, when}} for each channel (youtube under "youtube").
- dslog doc `<YYYY-MM-DD-HHMM>-hlweekly`.
