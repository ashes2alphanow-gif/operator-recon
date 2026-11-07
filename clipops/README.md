# CLIPOPS — Alpha 2 Unfiltered

A clip team that runs on your laptop. It finds source video, pulls the moments that fit the brand, cuts vertical Shorts with captions, writes the copy in channel voice, and queues them into post slots.

## The team

| Role | Who | Job |
|---|---|---|
| Scout | code (yt-dlp) | Finds source video in three lanes: your footage, creators who gave permission, and Creative Commons search. Ranks search hits by views against channel size, so small channels with a breakout video rank first. |
| Analyst | Claude | Reads the full transcript. Picks the moments that hook in 2 seconds, stand alone, and fit a pillar. Flags anything on the hard-no list. |
| Gate | code | Recomputes the scores, enforces hard-no and the score floor, and drops overlapping picks. |
| Packager | Claude | Writes the title, on-screen hook, closing take, pinned comment, and **your VO script**. |
| Editor | code (ffmpeg) | Builds a 1080x1920 Short: optional open card, the clip with a hook banner and burned captions at -14 LUFS, then an end card. Your voice memo drives the cards. |
| Rights Officer | code | Holds back anything that isn't your footage until your VO is in the folder. Adds credit lines to descriptions. |
| Publisher | code | Puts clips into the next open slot. Builds a post kit for manual upload, or uploads through the API with a scheduled publish time. |

Brand pillars, the hard-no list, sources, and post slots all live in `config.yaml`.

## Two rules the money depends on

1. **Commentary is the product.** YouTube's reused-content policy doesn't care about permission. Licensed clips with nothing of yours added still get a channel rejected from YPP or demonetized. Your VO, roughly 5 seconds at the open and 10 at the close, is what makes each Short yours. The Packager writes the script. You read it into your phone.
2. **Your own footage is the cleanest lane.** Drop talking-head or field-note recordings into `own_footage/` and they skip the VO requirement.

## Setup (once, ~15 min)

```bash
# needs Python 3.11+ and ffmpeg on PATH
cd clipops
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # or: ant auth login
# own footage transcription (optional):  pip install faster-whisper
```

Edit `config.yaml`: set `timezone` and `post_slots`, and add any creators who gave you clip permission under `allowlist` (keep the proof).

## Daily loop (~20 min of your time)

```bash
python -m clipops daily          # scout -> analyze -> render -> queue
```

1. `queue` lists **READY** and **NEEDS_VO**. For each NEEDS_VO clip, open `media/<video>/<clip>/vo_script.txt` and record `vo_close.m4a` (plus `vo_open.m4a` if you want an open card) into the same folder. Phone voice memo is fine.
2. `python -m clipops render`. Clips with VO move to READY.
3. Watch `final.mp4` before it posts. Kill bad ones with `python -m clipops reject <id>`.
4. `python -m clipops post -n 3` builds kits in `ready/<date>/<time>_<clip>/` with `video.mp4` and `post.txt`.
5. Upload each kit from YouTube Studio or the YouTube app. Paste the title and description, then pin the comment.
6. `python -m clipops posted <clip_id> <youtube_id>`
7. Weekly: `python -m clipops stats` shows views by pillar. Spend more on the pillar that's winning.

Optional automation: `0 5 * * * cd ~/clipops && .venv/bin/python -m clipops daily >> data/daily.log 2>&1`

## Moving to API uploads

YouTube API projects that haven't been audited upload as **locked private**. Stay on `publish.mode: manual` until the audit clears.

1. Google Cloud Console: create a project, enable **YouTube Data API v3**, and create an OAuth client ID of type *Desktop app*. Download it as `clipops/client_secret.json`.
2. Run `python -m clipops stats` once to sign in. This writes `data/token.json`. Stats work before the audit.
3. Submit the YouTube API Services audit form. Expect weeks.
4. Once approved, set `publish.mode: api`. `post` then uploads with a scheduled `publishAt`.

## Limits

- YouTube blocks bulk downloads from some IPs. If yt-dlp starts failing, update it first: `pip install -U yt-dlp`.
- The CC search filter relies on YouTube's search parameter. The Scout re-checks each video's license field before anything enters the queue.
- Fair use is off by default (`allow_unlicensed_with_commentary: false`). Turning it on is your call, and it carries copyright-strike risk on the channel meant to pay bills.
- Tests: `python -m unittest discover tests` (offline: rights gate, scoring, captions, full render, post kit).
